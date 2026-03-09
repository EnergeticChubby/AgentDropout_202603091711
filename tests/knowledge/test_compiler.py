from AgentDropout.knowledge.compiler import KnowledgeCompiler
from AgentDropout.knowledge.proposition import Proposition


def test_knowledge_compiler_promotes_final_answer():
    compiler = KnowledgeCompiler()
    props = [
        Proposition(
            proposition_id="p1",
            text="The answer is A",
            source_node="n1",
            source_role="solver",
        )
    ]
    plan = compiler.compile(props, "mmlu")
    assert len(plan) == 1
    assert plan[0].target_scope == "verified_shared"
