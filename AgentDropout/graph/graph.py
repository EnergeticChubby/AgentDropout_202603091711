import shortuuid
from typing import Any, List, Optional, Dict
from abc import ABC
import numpy as np
import torch
import asyncio

from AgentDropout.graph.node import Node
from AgentDropout.agents.agent_registry import AgentRegistry
import random
from dropout_scoring.edge_score import EdgeRiskWeights, compute_state_aware_edge_scores
from dropout_scoring.node_score import NodeRiskWeights, compute_state_aware_node_scores

class Graph(ABC):
    """
    A framework for managing and executing a network of nodes using a language model.

    This class enables the creation of a graph structure for processing and analyzing data. Each node
    in the graph can perform specific operations, allowing for complex data processing workflows.
    The graph supports integration with language models, making it suitable for tasks that require
    natural language processing capabilities.

    The communication of the node depends on the node.spatial_predecessors and node.spatial_successors.
    
    Attributes:
        domain (str): The domain for which this graph is used.
        llm_name (str): The name of the llm that used for processing within the nodes.
        nodes (dict): A collection of nodes, each identified by a unique UUID.

    Methods:
        build_graph(): Method to be implemented for constructing the graph structure.
        add_node(node): Adds a new node to the graph with a unique identifier.
        run(inputs, num_steps=10, single_agent=False): Executes the graph for a specified number of steps, processing provided inputs.
    """

    def __init__(self, 
                domain: str,
                llm_name: Optional[str],
                agent_names: List[str],
                decision_method: str,
                optimized_spatial:bool = False,
                initial_spatial_probability: float = 0.5,
                fixed_spatial_masks:List[List[int]] = None,
                optimized_temporal:bool = False,
                diff:bool = False,
                dec:bool = False,
                rounds: int = 1,
                initial_temporal_probability: float = 0.5,
                fixed_temporal_masks:List[List[int]] = None,
                node_kwargs:List[Dict] = None,
                telemetry_collector: Any = None,
                state_observer: Any = None,
                state_aware_node: bool = False,
                state_aware_edge: bool = False,
                node_risk_weights: Optional[Dict[str, float]] = None,
                edge_risk_weights: Optional[Dict[str, float]] = None,
                ):
        
        self.fixed_spatial_masks = torch.tensor(fixed_spatial_masks)
        self.fixed_temporal_masks = torch.tensor(fixed_temporal_masks)
        if fixed_spatial_masks is None:
            fixed_spatial_masks = [[1 if i!=j else 0 for j in range(len(agent_names))] for i in range(len(agent_names))]
        if fixed_temporal_masks is None:
            fixed_temporal_masks = [[1 for j in range(len(agent_names))] for i in range(len(agent_names))]
        fixed_spatial_masks = torch.tensor(fixed_spatial_masks).view(-1)
        fixed_temporal_masks = torch.tensor(fixed_temporal_masks).view(-1)
        # print(fixed_temporal_masks)
        assert len(fixed_spatial_masks)==len(agent_names)*len(agent_names),"The fixed_spatial_masks doesn't match the number of agents"
        assert len(fixed_temporal_masks)==len(agent_names)*len(agent_names),"The fixed_temporal_masks doesn't match the number of agents"
        
        self.id:str = shortuuid.ShortUUID().random(length=4)
        self.domain:str = domain
        self.llm_name:str = llm_name
        self.agent_names:List[str] = agent_names
        self.optimized_spatial = optimized_spatial
        self.optimized_temporal = optimized_temporal
        self.decision_node:Node = AgentRegistry.get(decision_method, **{"domain":self.domain,"llm_name":self.llm_name})
        self.nodes:Dict[str,Node] = {}
        self.potential_spatial_edges:List[List[str, str]] = []
        self.potential_temporal_edges:List[List[str,str]] = []
        self.node_kwargs = node_kwargs if node_kwargs is not None else [{} for _ in agent_names]
        self.diff=diff
        self.rounds=rounds
        # self.dec=False
        self.dec_1=False
        self.skip_nodes = []
        self.telemetry_collector = telemetry_collector
        self.state_observer = state_observer
        self.state_aware_node = state_aware_node
        self.state_aware_edge = state_aware_edge
        self.node_risk_weights = NodeRiskWeights(**(node_risk_weights or {}))
        self.edge_risk_weights = EdgeRiskWeights(**(edge_risk_weights or {}))
        self.latest_observer_output = None
        self.latest_risks = {
            "node_repeat": {},
            "node_consensus": {},
            "node_capacity": {},
            "edge_repeatflow": {},
            "edge_echo": {},
            "edge_capacityflow": {},
        }

        self.init_nodes() # add nodes to the self.nodes
        self.init_potential_edges() # add potential edges to the self.potential_spatial/temporal_edges
        
        init_spatial_logit = torch.log(torch.tensor(initial_spatial_probability / (1 - initial_spatial_probability))) if optimized_spatial else 10.0
        init_temporal_logit = torch.log(torch.tensor(initial_temporal_probability / (1 - initial_temporal_probability))) if optimized_temporal else 10.0

        print(self.potential_spatial_edges)
        if dec:
            # self.decision_masks = torch.nn.Parameter(torch.ones(5),requires_grad=False)
            self.decision_logits = torch.ones(5) * torch.log(torch.tensor(1.0))
            # self.spatial_logits_1 = None
            # self.temporal_logits_1 = None
            # print(self.decision_mask)
        if not diff:
            self.spatial_masks = torch.nn.Parameter(fixed_spatial_masks,requires_grad=False)  # fixed edge masks
            self.spatial_logits = torch.nn.Parameter(torch.ones(len(self.potential_spatial_edges), requires_grad=optimized_spatial) * init_spatial_logit,requires_grad=optimized_spatial) # trainable edge logits
            self.temporal_logits = torch.nn.Parameter(torch.ones(len(self.potential_temporal_edges), requires_grad=optimized_temporal) * init_temporal_logit,requires_grad=optimized_temporal) # trainable edge logits
            self.temporal_masks = torch.nn.Parameter(fixed_temporal_masks,requires_grad=False)  # fixed edge masks
            if dec:
                self.spatial_logits_1 = torch.nn.Parameter(torch.ones(len(self.potential_spatial_edges), requires_grad=optimized_spatial) * init_spatial_logit,requires_grad=optimized_spatial)
                self.temporal_logits_1 = torch.nn.Parameter(torch.ones(len(self.potential_temporal_edges), requires_grad=optimized_temporal) * init_temporal_logit,requires_grad=optimized_temporal)
            # print(self.spatial_logits)
            # print(self.spatial_masks)
        else:
            if dec:
                self.spatial_logits_1 = torch.nn.ParameterList([torch.nn.Parameter(torch.ones(len(self.potential_spatial_edges), requires_grad=optimized_spatial) * init_spatial_logit,requires_grad=optimized_spatial) for _ in range(rounds)])
                self.temporal_logits_1 = torch.nn.ParameterList([torch.nn.Parameter(torch.ones(len(self.potential_temporal_edges), requires_grad=optimized_temporal) * init_temporal_logit,requires_grad=optimized_temporal) for _ in range(rounds-1)])
            self.spatial_masks = torch.nn.ParameterList([torch.nn.Parameter(fixed_spatial_masks.clone(), requires_grad=False) for _ in range(rounds)])  # fixed edge masks
            self.spatial_logits = torch.nn.ParameterList([torch.nn.Parameter(torch.ones(len(self.potential_spatial_edges), requires_grad=optimized_spatial) * init_spatial_logit,requires_grad=optimized_spatial) for _ in range(rounds)])
            self.temporal_logits = torch.nn.ParameterList([torch.nn.Parameter(torch.ones(len(self.potential_temporal_edges), requires_grad=optimized_temporal) * init_temporal_logit,requires_grad=optimized_temporal) for _ in range(rounds-1)])
            self.temporal_masks = torch.nn.ParameterList([torch.nn.Parameter(fixed_temporal_masks.clone(), requires_grad=False) for _ in range(rounds-1)])

    def _scaled_node_weights(self) -> NodeRiskWeights:
        if self.latest_observer_output is None:
            return self.node_risk_weights
        scale = 1.0 + max(0.0, 0.5 - float(self.latest_observer_output.viability_score))
        return NodeRiskWeights(
            repeat=self.node_risk_weights.repeat * scale,
            consensus=self.node_risk_weights.consensus * scale,
            capacity=self.node_risk_weights.capacity * scale,
        )

    def _scaled_edge_weights(self) -> EdgeRiskWeights:
        if self.latest_observer_output is None:
            return self.edge_risk_weights
        scale = 1.0 + max(0.0, 0.5 - float(self.latest_observer_output.viability_score))
        return EdgeRiskWeights(
            repeatflow=self.edge_risk_weights.repeatflow * scale,
            echo=self.edge_risk_weights.echo * scale,
            capacityflow=self.edge_risk_weights.capacityflow * scale,
        )
        
    @property
    def spatial_adj_matrix(self):
        matrix = np.zeros((len(self.nodes), len(self.nodes)))
        for i, node1_id in enumerate(self.nodes):
            for j, node2_id in enumerate(self.nodes):
                if self.nodes[node2_id] in self.nodes[node1_id].spatial_successors: 
                    matrix[i, j] = 1
        return matrix

    @property
    def temporal_adj_matrix(self):
        matrix = np.zeros((len(self.nodes), len(self.nodes)))
        for i, node1_id in enumerate(self.nodes):
            for j, node2_id in enumerate(self.nodes):
                if self.nodes[node2_id] in self.nodes[node1_id].temporal_successors: 
                    matrix[i, j] = 1
        return matrix

    @property
    def num_edges(self):
        num_edges = 0
        for node in self.nodes.values():
            num_edges += len(node.spatial_successors)
        return num_edges
    
    @property
    def num_nodes(self):
        return len(self.nodes)

    def find_node(self, id: str):
        if id in self.nodes.keys():
            return self.nodes[id]
        raise Exception(f"Node not found: {id} among "
                        f"{[node.id for node in self.nodes.values()]}")
        
    def add_node(self, node: Node):
        node_id = node.id if node.id is not None else shortuuid.ShortUUID().random(length=4)
        while node_id in self.nodes:
            node_id = shortuuid.ShortUUID().random(length=4)
        node.id = node_id
        self.nodes[node_id] = node
        return node
    
    def init_nodes(self):
        """
        Creates and adds new nodes to the graph.
        """
        for agent_name,kwargs in zip(self.agent_names,self.node_kwargs):
            if agent_name in AgentRegistry.registry:
                kwargs["domain"] = self.domain
                kwargs["llm_name"] = self.llm_name
                agent_instance = AgentRegistry.get(agent_name, **kwargs)
                self.add_node(agent_instance)
    
    def init_potential_edges(self):
        """
        Creates and potential edges to the graph.
        """
        for node1_id in self.nodes.keys():
            for node2_id in self.nodes.keys():
                self.potential_spatial_edges.append([node1_id,node2_id])
                self.potential_temporal_edges.append([node1_id,node2_id])

    def clear_spatial_connection(self):
        """
        Clear all the spatial connection of the nodes in the graph.
        """
        for node_id in self.nodes.keys():
            self.nodes[node_id].spatial_predecessors = []
            self.nodes[node_id].spatial_successors = []
        self.decision_node.spatial_predecessors = []
        self.decision_node.spatial_successors = []
    
    def clear_temporal_connection(self):
        """
        Clear all the temporal connection of the nodes in the graph.
        """
        for node_id in self.nodes.keys():
            self.nodes[node_id].temporal_predecessors = []
            self.nodes[node_id].temporal_successors = []

    def connect_decision_node(self):
        for node_id in self.nodes.keys():
            self.nodes[node_id].add_successor(self.decision_node)



    def construct_spatial_connection(self, temperature: float = 1.0, threshold: float = None,): # temperature must >= 1.0
        self.clear_spatial_connection()
        log_probs = [torch.tensor(0.0, requires_grad=self.optimized_spatial)]
        
        for potential_connection, edge_logit, edge_mask in zip(self.potential_spatial_edges, self.spatial_logits, self.spatial_masks):
            out_node:Node = self.find_node(potential_connection[0])
            in_node:Node = self.find_node(potential_connection[1])
            # print(out_node)
            if edge_mask == 0.0:
                continue
            elif edge_mask == 1.0 and self.optimized_spatial==False:
                if not self.check_cycle(in_node, {out_node}):
                    out_node.add_successor(in_node,'spatial')
                    # print(potential_connection)
                continue
            if not self.check_cycle(in_node, {out_node}):
                # print("@@@@@@@@@@@")
                edge_prob = torch.sigmoid(edge_logit / temperature)
                if threshold:
                    edge_prob = torch.tensor(1 if edge_prob > threshold else 0)
                if torch.rand(1) < edge_prob:
                    out_node.add_successor(in_node,'spatial')
                    log_probs.append(torch.log(edge_prob))
                else:
                    log_probs.append(torch.log(1 - edge_prob))
                    
        return torch.sum(torch.stack(log_probs))
    
    
    
    def construct_spatial_connection_diff(self, round:int = 0, temperature: float = 1.0, threshold: float = None,): # temperature must >= 1.0
        self.clear_spatial_connection()
        log_probs = [torch.tensor(0.0, requires_grad=self.optimized_spatial)]
        
        for potential_connection, edge_logit, edge_mask in zip(self.potential_spatial_edges, self.spatial_logits[round], self.spatial_masks[round]):
            out_node:Node = self.find_node(potential_connection[0])
            in_node:Node = self.find_node(potential_connection[1])
            out_id = list(self.nodes).index(out_node.id)
            in_id = list(self.nodes).index(in_node.id)
            if edge_mask == 0.0:
                continue
            elif edge_mask == 1.0 and self.optimized_spatial==False:
                # if round == self.rounds-1 and self.dec_1 and (self.decision_masks[in_id]==0 or self.decision_masks[out_id]==0):
                #     print(11111)
                #     continue
                if not self.check_cycle(in_node, {out_node}):
                    out_node.add_successor(in_node,'spatial')
                    # print(potential_connection)
                continue
            if not self.check_cycle(in_node, {out_node}):
                edge_prob = torch.sigmoid(edge_logit / temperature)
                if threshold:
                    edge_prob = torch.tensor(1 if edge_prob > threshold else 0)
                if torch.rand(1) < edge_prob:
                    out_node.add_successor(in_node,'spatial')
                    log_probs.append(torch.log(edge_prob))
                else:
                    log_probs.append(torch.log(1 - edge_prob))
                    
        return torch.sum(torch.stack(log_probs))
    
    def construct_temporal_connection(self, round:int = 0, temperature: float = 1.0, threshold: float = None,):  # temperature must >= 1.0
        self.clear_temporal_connection()
        log_probs = [torch.tensor(0.0, requires_grad=self.optimized_temporal)]
        if round == 0:
            return torch.sum(torch.stack(log_probs))  
        for potential_connection, edge_logit, edge_mask in zip(self.potential_temporal_edges, self.temporal_logits, self.temporal_masks):
            out_node:Node = self.find_node(potential_connection[0])
            in_node:Node = self.find_node(potential_connection[1])
            if edge_mask == 0.0:
                continue
            elif edge_mask == 1.0 and self.optimized_temporal==False:
                if not self.check_cycle(in_node, {out_node}):
                    out_node.add_successor(in_node,'temporal')
                    # print(potential_connection)
                continue
            
            edge_prob = torch.sigmoid(edge_logit / temperature)
            if threshold:
                edge_prob = torch.tensor(1 if edge_prob > threshold else 0)
            if torch.rand(1) < edge_prob:
                out_node.add_successor(in_node,'temporal')
                log_probs.append(torch.log(edge_prob))
            else:
                log_probs.append(torch.log(1 - edge_prob))
                    
        return torch.sum(torch.stack(log_probs))


    def construct_temporal_connection_diff(self, round:int = 0, temperature: float = 1.0, threshold: float = None,):  # temperature must >= 1.0
        self.clear_temporal_connection()
        log_probs = [torch.tensor(0.0, requires_grad=self.optimized_temporal)]
        if round == 0:
            return torch.sum(torch.stack(log_probs))  
        for potential_connection, edge_logit, edge_mask in zip(self.potential_temporal_edges, self.temporal_logits[round-1], self.temporal_masks[round-1]):
            out_node:Node = self.find_node(potential_connection[0])
            in_node:Node = self.find_node(potential_connection[1])
            if edge_mask == 0.0:
                continue
            elif edge_mask == 1.0 and self.optimized_temporal==False:
                if not self.check_cycle(in_node, {out_node}):
                    out_node.add_successor(in_node,'temporal')
                continue
            
            edge_prob = torch.sigmoid(edge_logit / temperature)
            if threshold:
                edge_prob = torch.tensor(1 if edge_prob > threshold else 0)
            if torch.rand(1) < edge_prob:
                out_node.add_successor(in_node,'temporal')
                log_probs.append(torch.log(edge_prob))
            else:
                log_probs.append(torch.log(1 - edge_prob))
                    
        return torch.sum(torch.stack(log_probs))


    def run(self, inputs: Any, 
                  num_rounds:int = 3, 
                  max_tries: int = 3, 
                  max_time: int = 600,) -> List[Any]:
        # inputs:{'task':"xxx"}
        log_probs = 0
        for round in range(num_rounds):
            log_probs += self.construct_spatial_connection()
            log_probs += self.construct_temporal_connection(round)
            
            in_degree = {node_id: len(node.spatial_predecessors) for node_id, node in self.nodes.items()}
            zero_in_degree_queue = [node_id for node_id, deg in in_degree.items() if deg == 0]

            while zero_in_degree_queue:
                current_node_id = zero_in_degree_queue.pop(0)
                tries = 0
                while tries < max_tries:
                    try:
                        self.nodes[current_node_id].execute(inputs) # output is saved in the node.outputs
                        break
                    except Exception as e:
                        print(f"Error during execution of node {current_node_id}: {e}")
                    tries += 1
                for successor in self.nodes[current_node_id].spatial_successors:
                    if successor.id not in self.nodes.keys():
                        continue
                    in_degree[successor.id] -= 1
                    if in_degree[successor.id] == 0:
                        zero_in_degree_queue.append(successor.id)
            
            self._update_state_features(case_id=inputs.get("task", self.id), round_id=round)
            self.update_memory()
            
        self.connect_decision_node()
        self.decision_node.execute(inputs)
        final_answers = self.decision_node.outputs
        if len(final_answers) == 0:
            final_answers.append("No answer of the decision node")
        if self.telemetry_collector is not None:
            self.telemetry_collector.flush()
            
        return final_answers, log_probs

    async def arun(self, input: Dict[str,str], 
                  num_rounds:int = 3, 
                  max_tries: int = 3, 
                  max_time: int = 6000,
                  skip: bool=False,
                  case: bool=False) -> List[Any]:
        # inputs:{'task':"xxx"}
        log_probs = 0
        log_probs_skip = 0
        all_answers = []
        for round in range(num_rounds):
            round_answers = {}
            if not self.diff:
                log_probs += self.construct_spatial_connection()
                log_probs += self.construct_temporal_connection(round)
            else:
                log_probs += self.construct_spatial_connection_diff(round)
                log_probs += self.construct_temporal_connection_diff(round)
            
            # print(self.num_edges)

            in_degree = {node_id: len(node.spatial_predecessors) for node_id, node in self.nodes.items()}
            zero_in_degree_queue = [node_id for node_id, deg in in_degree.items() if deg == 0]

            in_degree_t = {node_id: len(node.temporal_predecessors) for node_id, node in self.nodes.items()}
            zero_in_degree_queue_t = [node_id for node_id, deg in in_degree_t.items() if deg == 0]

            selected_index=-1

            if round <= 5 and skip:
                # log_probs = 0
                min_logit=100
                min_node=None
                min_loss=100
                loss_t_list = []
                loss_f_list = []
                log_list=[]
                for node_id, node in self.nodes.items():
                    in_id = list(self.nodes).index(node_id)
                    count=0
                    logits_count=0.
                    loss_t=0
                    loss_f=0
                    t=1.0
                    
                    for last_node in node.spatial_successors:
                        last_id = list(self.nodes).index(last_node.id)
                        count+=1
                        # logits_count+=torch.sigmoid(t*self.spatial_logits_1[round][in_id*5+last_id])
                        logits_count+=t*self.spatial_logits_1[round][in_id*5+last_id]
                        loss_t+=torch.log(1-torch.sigmoid(self.spatial_logits_1[round][in_id*5+last_id]))
                        loss_f+=torch.log(torch.sigmoid(self.spatial_logits_1[round][in_id*5+last_id]))
                    for last_node in node.spatial_predecessors:
                        last_id = list(self.nodes).index(last_node.id)
                        count+=1
                        # logits_count+=torch.sigmoid(t*self.spatial_logits_1[round][last_id*5+in_id])
                        logits_count+=t*self.spatial_logits_1[round][last_id*5+in_id]
                        loss_t+=torch.log(1-torch.sigmoid(self.spatial_logits_1[round][last_id*5+in_id]))
                        loss_f+=torch.log(torch.sigmoid(self.spatial_logits_1[round][last_id*5+in_id]))
                    # for last_node in node.temporal_predecessors:
                    #     last_id = list(self.nodes).index(last_node.id)
                    #     count+=1
                    #     # logits_count+=torch.sigmoid(t*self.temporal_logits_1[round-1][last_id*5+in_id])
                    #     logits_count+=t*self.temporal_logits_1[round-1][last_id*5+in_id]
                    #     loss_t+=torch.log(1-torch.sigmoid(self.temporal_logits_1[round-1][last_id*5+in_id]))
                    #     loss_f+=torch.log(torch.sigmoid(self.temporal_logits_1[round-1][last_id*5+in_id]))
                    log_list.append(logits_count)
                    if count==0:
                        count=1.0
                    loss_t_list.append(loss_t)
                    loss_f_list.append(loss_f)
                    # if logits_count / count < min_logit:
                    #     min_logit = logits_count / count
                    #     min_avg = logits_count / count
                    #     min_node = node_id
                    # elif logits_count / count == min_logit:
                    #     if len(node.spatial_predecessors)+len(node.temporal_predecessors)>len(self.find_node(min_node).spatial_predecessors)+len(self.find_node(min_node).temporal_predecessors):
                    #         # print(1111)
                    #         min_node = node_id
                    
                p = torch.softmax(torch.tensor(log_list),dim=0)
                selected_index = torch.multinomial(p, num_samples=1, replacement=False)
                # selected_index = list(self.nodes).index(min_node)
                # selected_index = 1
                for i in range(5):
                    if i==selected_index:
                        log_probs_skip += 4.0*loss_t_list[i]
                    else:
                        log_probs_skip += loss_f_list[i]
                # print(selected_index)
                # if self.skip_nodes:
                #     self.skip_nodes[round] = random.randint(0, 4)

            # for i in range(len(self.skip_nodes)):
            #     self.skip_nodes[i] = random.randint(0, 4)
            while zero_in_degree_queue:
                # if round==1 and i<2:
                #     continue
                current_node_id = zero_in_degree_queue.pop(0)
                tries = 0
                while tries < max_tries:
                    try:
                        # if current_node_id in need_skip:
                        if list(self.nodes).index(current_node_id) == selected_index and skip:
                            # print(111)
                            # if selected_index==1:
                            self.find_node(current_node_id).outputs = ['None.']
                            break
                        elif self.skip_nodes:
                            if list(self.nodes).index(current_node_id) == self.skip_nodes[round]:
                                self.find_node(current_node_id).outputs = ['None.']
                                break
                        await asyncio.wait_for(self.nodes[current_node_id].async_execute(input),timeout=max_time) # output is saved in the node.outputs
                        # print(self.find_node(current_node_id).outputs)
                        break
                    except Exception as e:
                        print(f"Error during execution of node {current_node_id}: {e}")
                    tries += 1
                for successor in self.nodes[current_node_id].spatial_successors:
                    if successor.id not in self.nodes.keys():
                        continue
                    in_degree[successor.id] -= 1
                    if in_degree[successor.id] == 0:
                        zero_in_degree_queue.append(successor.id)
            for node in self.nodes:
                round_answers[self.nodes[node].role+str(node)] = self.nodes[node].outputs
            all_answers.append(round_answers)
            self._update_state_features(case_id=input.get("task", self.id), round_id=round)
            self.update_memory()
        
        # if self.dec_1==False:
        if len(self.potential_spatial_edges)>0:
            self.connect_decision_node()
            await self.decision_node.async_execute(input)
            final_answers = self.decision_node.outputs
        else:
            final_answers = list(self.nodes.values())[0].outputs
        if len(final_answers) == 0:
            final_answers.append("No answer of the decision node")
        if self.telemetry_collector is not None:
            self.telemetry_collector.flush()
        # print(log_probs)
        # if skip:
        #     return final_answers, selected_index
        # else:
        if skip:
            return final_answers, log_probs_skip
        elif case:
            return final_answers, log_probs, all_answers
        else:
            return final_answers, log_probs

    def _active_edges(self) -> List[List[str]]:
        edges = []
        for src_id, node in self.nodes.items():
            for succ in node.spatial_successors:
                edges.append([src_id, succ.id, "spatial"])
            for succ in node.temporal_successors:
                edges.append([src_id, succ.id, "temporal"])
        return edges

    def _update_state_features(self, case_id: str, round_id: int):
        if self.telemetry_collector is None:
            return
        node_outputs = {}
        for node_id, node in self.nodes.items():
            if isinstance(node.outputs, list) and len(node.outputs) > 0:
                node_outputs[node_id] = str(node.outputs[-1])
            else:
                node_outputs[node_id] = str(node.outputs)
        telemetry = self.telemetry_collector.record_round(
            case_id=case_id,
            round_id=round_id,
            node_outputs=node_outputs,
            active_edges=self._active_edges(),
        )
        features = self.telemetry_collector.get_latest_features()
        self.latest_risks = {
            "node_repeat": features.node_repeat_risk,
            "node_consensus": features.node_consensus_risk,
            "node_capacity": features.node_capacity_risk,
            "edge_repeatflow": features.edge_repeatflow_risk,
            "edge_echo": features.edge_echo_risk,
            "edge_capacityflow": features.edge_capacityflow_risk,
        }
        if self.state_observer is not None:
            self.latest_observer_output = self.state_observer.update(telemetry)
    
    def update_memory(self):
        for id,node in self.nodes.items():
            node.update_memory()
    
    def check_cycle(self, new_node, target_nodes):
        if new_node in target_nodes:
            return True
        for successor in new_node.spatial_successors:
            if self.check_cycle(successor, target_nodes):
                return True
        return False

    def update_masks(self, pruning_rate: float) -> torch.Tensor:
        if self.optimized_spatial:
            num_edges = (self.spatial_masks > 0).sum()
            num_masks = (self.spatial_masks == 0).sum()
            prune_num_edges = torch.round(num_edges*pruning_rate) if torch.round(num_edges*pruning_rate)>0 else 1
            _edge_logits = self.spatial_logits.clone()
            if self.state_aware_edge:
                base_scores = {}
                for idx, potential_connection in enumerate(self.potential_spatial_edges):
                    key = f"{potential_connection[0]}->{potential_connection[1]}:spatial"
                    base_scores[key] = float(_edge_logits[idx].item())
                edge_scores = compute_state_aware_edge_scores(
                    base_scores=base_scores,
                    repeatflow_risk=self.latest_risks.get("edge_repeatflow", {}),
                    echo_risk=self.latest_risks.get("edge_echo", {}),
                    capacityflow_risk=self.latest_risks.get("edge_capacityflow", {}),
                    weights=self._scaled_edge_weights(),
                )
                for idx, potential_connection in enumerate(self.potential_spatial_edges):
                    key = f"{potential_connection[0]}->{potential_connection[1]}:spatial"
                    _edge_logits[idx] = edge_scores.get(key, float(_edge_logits[idx].item()))
            min_edge_logit = _edge_logits.min()
            _edge_logits[self.spatial_masks == 0] = min_edge_logit - 1.0
            sorted_edges_idx = torch.argsort(_edge_logits)
            prune_idx = sorted_edges_idx[:int(prune_num_edges + num_masks)]
            self.spatial_masks[prune_idx] = 0
        
        if self.optimized_temporal:
            num_edges = (self.temporal_masks > 0).sum()
            num_masks = (self.temporal_masks == 0).sum()
            prune_num_edges = torch.round(num_edges*pruning_rate) if torch.round(num_edges*pruning_rate)>0 else 1
            _edge_logits = self.temporal_logits.clone()
            if self.state_aware_edge:
                base_scores = {}
                for idx, potential_connection in enumerate(self.potential_temporal_edges):
                    key = f"{potential_connection[0]}->{potential_connection[1]}:temporal"
                    base_scores[key] = float(_edge_logits[idx].item())
                edge_scores = compute_state_aware_edge_scores(
                    base_scores=base_scores,
                    repeatflow_risk=self.latest_risks.get("edge_repeatflow", {}),
                    echo_risk=self.latest_risks.get("edge_echo", {}),
                    capacityflow_risk=self.latest_risks.get("edge_capacityflow", {}),
                    weights=self._scaled_edge_weights(),
                )
                for idx, potential_connection in enumerate(self.potential_temporal_edges):
                    key = f"{potential_connection[0]}->{potential_connection[1]}:temporal"
                    _edge_logits[idx] = edge_scores.get(key, float(_edge_logits[idx].item()))
            min_edge_logit = _edge_logits.min()
            _edge_logits[self.temporal_masks == 0] = min_edge_logit - 1.0
            sorted_edges_idx = torch.argsort(_edge_logits)
            prune_idx = sorted_edges_idx[:int(prune_num_edges + num_masks)]
            self.temporal_masks[prune_idx] = 0
        return self.spatial_masks, self.temporal_masks
    
    def update_masks_diff(self, pruning_rate: float) -> torch.Tensor:
        if self.optimized_spatial:
            for i in range(self.rounds):
                num_edges = (self.spatial_masks[i] > 0).sum()
                num_masks = (self.spatial_masks[i] == 0).sum()
                prune_num_edges = torch.round(num_edges*pruning_rate) if torch.round(num_edges*pruning_rate)>0 else 1
                _edge_logits = self.spatial_logits[i].clone()
                if self.state_aware_edge:
                    base_scores = {}
                    for idx, potential_connection in enumerate(self.potential_spatial_edges):
                        key = f"{potential_connection[0]}->{potential_connection[1]}:spatial"
                        base_scores[key] = float(_edge_logits[idx].item())
                    edge_scores = compute_state_aware_edge_scores(
                        base_scores=base_scores,
                        repeatflow_risk=self.latest_risks.get("edge_repeatflow", {}),
                        echo_risk=self.latest_risks.get("edge_echo", {}),
                        capacityflow_risk=self.latest_risks.get("edge_capacityflow", {}),
                        weights=self._scaled_edge_weights(),
                    )
                    for idx, potential_connection in enumerate(self.potential_spatial_edges):
                        key = f"{potential_connection[0]}->{potential_connection[1]}:spatial"
                        _edge_logits[idx] = edge_scores.get(key, float(_edge_logits[idx].item()))
                min_edge_logit = _edge_logits.min()
                _edge_logits[self.spatial_masks[i] == 0] = min_edge_logit - 1.0
                sorted_edges_idx = torch.argsort(_edge_logits)
                # _edge_logits = torch.cat([_edge_logits[:num_masks], _edge_logits[num_masks:][torch.randperm(len(_edge_logits)-num_masks)]])
                prune_idx = sorted_edges_idx[:int(prune_num_edges + num_masks)]
                self.spatial_masks[i][prune_idx] = 0
        
        if self.optimized_temporal:
            for i in range(self.rounds-1):
                num_edges = (self.temporal_masks[i] > 0).sum()
                num_masks = (self.temporal_masks[i] == 0).sum()
                prune_num_edges = torch.round(num_edges*pruning_rate) if torch.round(num_edges*pruning_rate)>0 else 1
                _edge_logits = self.temporal_logits[i].clone()
                if self.state_aware_edge:
                    base_scores = {}
                    for idx, potential_connection in enumerate(self.potential_temporal_edges):
                        key = f"{potential_connection[0]}->{potential_connection[1]}:temporal"
                        base_scores[key] = float(_edge_logits[idx].item())
                    edge_scores = compute_state_aware_edge_scores(
                        base_scores=base_scores,
                        repeatflow_risk=self.latest_risks.get("edge_repeatflow", {}),
                        echo_risk=self.latest_risks.get("edge_echo", {}),
                        capacityflow_risk=self.latest_risks.get("edge_capacityflow", {}),
                        weights=self._scaled_edge_weights(),
                    )
                    for idx, potential_connection in enumerate(self.potential_temporal_edges):
                        key = f"{potential_connection[0]}->{potential_connection[1]}:temporal"
                        _edge_logits[idx] = edge_scores.get(key, float(_edge_logits[idx].item()))
                min_edge_logit = _edge_logits.min()
                _edge_logits[self.temporal_masks[i] == 0] = min_edge_logit - 1.0
                sorted_edges_idx = torch.argsort(_edge_logits)
                # _edge_logits = torch.cat([_edge_logits[:num_masks], _edge_logits[num_masks:][torch.randperm(len(_edge_logits)-num_masks)]])
                prune_idx = sorted_edges_idx[:int(prune_num_edges + num_masks)]
                self.temporal_masks[i][prune_idx] = 0
        # self.spatial_logits_1 = self.spatial_logits.clone()
        # self.temporal_logits_1 = self.temporal_logits.clone()
        return self.spatial_masks, self.temporal_masks

    def update_masks_dec(self):
        num_nodes = len(self.nodes)
        spatial_matrix_train = [param.reshape((num_nodes, num_nodes)) for param in self.spatial_logits_1]
        temporal_matrix_train = [param.reshape((num_nodes, num_nodes)) for param in self.temporal_logits_1]
        # spatial_mask_train = [param.reshape((5, 5)) for param in self.spatial_masks]
        # temporal_mask_train = [param.reshape((5, 5)) for param in self.temporal_masks]

        node_ids = list(self.nodes.keys())
        for i in range(len(spatial_matrix_train)):
            min = 100
            min_node = -1
            struct_scores = {}
            for j in range(num_nodes):
                sum = torch.sum(spatial_matrix_train[i][j,:]).item() + torch.sum(spatial_matrix_train[i][:,j]).item()
                count = torch.sum(self.fixed_spatial_masks[j,:]).item() + torch.sum(self.fixed_spatial_masks[:,j]).item()
                count = count if count > 0 else 1.0
                struct_scores[node_ids[j]] = sum / count

            if self.state_aware_node:
                scored_nodes = compute_state_aware_node_scores(
                    struct_scores=struct_scores,
                    repeat_risk=self.latest_risks.get("node_repeat", {}),
                    consensus_risk=self.latest_risks.get("node_consensus", {}),
                    capacity_risk=self.latest_risks.get("node_capacity", {}),
                    weights=self._scaled_node_weights(),
                )
            else:
                scored_nodes = struct_scores

            for node_idx, node_id in enumerate(node_ids):
                node_score = scored_nodes.get(node_id, 0.0)
                if node_score < min:
                    min = node_score
                    min_node = node_idx
            # min_node=random.randint(0, 4)
            self.skip_nodes.append(min_node)
            for k in range(num_nodes):
                self.spatial_masks[i][min_node*num_nodes+k]=0
                self.spatial_masks[i][k*num_nodes+min_node]=0
            if i > 0:
                for k in range(num_nodes):
                    self.temporal_masks[i-1][k*num_nodes+min_node]=0
            if i < len(spatial_matrix_train) - 1:
                for k in range(num_nodes):
                    self.temporal_masks[i][min_node*num_nodes+k]=0
