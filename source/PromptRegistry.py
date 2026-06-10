import json

class PromptRegistry:
    PROMPTS = {
        "intent": "识别用户意图与约束，输出 JSON。",
        "brief": "根据 query 和 intent 生成写作任务书 JSON。",
        "planner": "生成结构化大纲 JSON。",
        "planner_criticle": "审查大纲并输出 need_fix。",
        "planner_opt": "根据审查意见优化大纲。",
        "search_query": "判断分节是否需要检索并生成查询语句。",
        "web_summary": "总结证据并输出置信度。",
        "draft": "根据前序信息生成初稿。",
        "draft_criticle": "验收初稿并给出修改意见。",
        "writer": "输出最终稿。",
    }

    @classmethod
    def load(cls, prompt_key: str) -> str:
        return cls.PROMPTS[prompt_key]

    
class StageSkillRegistry:
    @staticmethod
    def load_all() -> List[StageSkill]:
        return [
            StageSkill("intent", "intent_understanding_skill", "intent", "IntentParser", ["query"], ["intent", "rewrite_query", "number_constraint", "time_constraint", "holiday_constraint"]),
            StageSkill("brief", "brief_generation_skill", "brief", "BriefParser", ["query", "intent", "number_constraint", "time_constraint", "holiday_constraint"], ["brief", "main_goal", "success_criteria"]),
            StageSkill("planner", "planner_generation_skill", "planner", "PlannerParser", ["query", "brief"], ["planner"]),
            StageSkill("planner_criticle", "planner_critic_skill", "planner_criticle", "PlannerCriticParser", ["planner"], ["planner_criticle"]),
            StageSkill("planner_opt", "planner_opt_skill", "planner_opt", "PlannerOptParser", ["planner", "planner_criticle"], ["planner_opt"], condition="need_planner_opt"),
            StageSkill("search_query", "search_decision_skill", "search_query", "SearchQueryParser", ["query", "planner_final"], ["search_query"]),
            StageSkill("web_summary", "web_summary_skill", "web_summary", "WebSummaryParser", ["search_query", "search_results"], ["web_summary"], condition="need_web_summary"),
            StageSkill("draft", "draft_skill", "draft", "DraftParser", ["query", "intent", "brief", "planner_final", "web_summary"], ["draft"]),
            StageSkill("draft_criticle", "draft_critic_skill", "draft_criticle", "DraftCriticParser", ["draft", "success_criteria"], ["draft_criticle"]),
            StageSkill("writer", "writer_skill", "writer", "WriterParser", ["draft", "draft_criticle"], ["final_result"]),
        ]