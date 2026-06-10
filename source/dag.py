from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque

@dataclass
class DAGNode:
    node_id: str
    title: str
    task: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    termination_criteria: Optional[dict] = None
    max_iterations: int = 3
    status: str = "pending"
    result: Optional[dict] = None
    layer: int = -1  # 新增：节点所在层级，-1表示未计算


class DAG:
    def __init__(self) -> None:
        self.nodes: Dict[str, DAGNode] = {}

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, parent_id: str, child_id: str) -> None:
        self.nodes[child_id].dependencies.append(parent_id)

    def get_ready_nodes(self) -> List[DAGNode]:
        ready = []
        for node in self.nodes.values():
            if node.status != "pending":
                continue
            deps_done = all(self.nodes[dep].status == "done" for dep in node.dependencies)
            if deps_done:
                ready.append(node)
        return ready

    def mark_done(self, node_id: str, result: dict) -> None:
        self.nodes[node_id].status = "done"
        self.nodes[node_id].result = result

    def all_done(self) -> bool:
        return all(n.status == "done" for n in self.nodes.values())
    
    def calculate_layers(self) -> None:
        """
        计算每个节点的层级（拓扑排序）
        根节点（无依赖）在第0层
        """
        # 初始化所有节点的层级为-1
        for node in self.nodes.values():
            node.layer = -1

        # 使用队列进行 BFS 拓扑排序
        queue = deque()

        # 找到所有无依赖的节点（根节点）作为第0层
        for node in self.nodes.values():
            if not node.dependencies:
                node.layer = 0
                queue.append(node.node_id)

        # BFS 计算层级
        while queue:
            current_id = queue.popleft()
            current_node = self.nodes[current_id]

            # 找到所有依赖当前节点的节点
            for node_id, node in self.nodes.items():
                if current_id in node.dependencies and node.layer == -1:
                    # 检查该节点的所有依赖是否都已计算层级
                    all_deps_calculated = all(
                        self.nodes[dep].layer != -1 
                        for dep in node.dependencies
                    )
                    if all_deps_calculated:
                        # 层级 = max(依赖节点的层级) + 1
                        max_dep_layer = max(
                            self.nodes[dep].layer 
                            for dep in node.dependencies
                        )
                        node.layer = max_dep_layer + 1
                        queue.append(node_id)
                        
    def get_nodes_by_layer(self) -> Dict[int, List[DAGNode]]:
        """按层级分组获取所有节点"""
        layers = {}
        for node in self.nodes.values():
            if node.layer not in layers:
                layers[node.layer] = []
            layers[node.layer].append(node)
        return dict(sorted(layers.items()))
    
    def print_layer_info(self) -> None:
        """打印层级信息（用于调试）"""
        layers = self.get_nodes_by_layer()
        for layer_num in sorted(layers.keys()):
            print(f"\n第 {layer_num} 层:")
            for node in layers[layer_num]:
                indent = "  " * layer_num
                print(f"{indent}├─ {node.node_id}: {node.title}")
                print(f"{indent}   依赖: {node.dependencies}")
                
    def build_plan_dag(self, outline, brief):
        """
        将研究大纲变成 DAG。
        DAG 中每个节点是一个可执行研究任务。
        """
        # 创建根节点 - 注意这里要创建 DAGNode 对象
        root = DAGNode(
            node_id="ROOT",
            title=brief["main_goal"],
            task=brief["main_goal"]  # 使用 task 字段
        )
        self.add_node(root)

        sections_set = []
        for section in outline["sections"]:
            sections_set.append(section["id"])
        
        for section in outline["sections"]:
            # 创建章节节点
            section_node = DAGNode(
                node_id=section["id"],
                title=section["sub_goal"],
                task="\n-".join(section["key_points"]),
                dependencies = [idx for idx in section["depend_ids"] if idx in sections_set]
            )
            self.add_node(section_node)
        
        return self

outline = {'raise_error': '', 'title': '入党申请书', 'sections': [{'id': 's1', 'sub_goal': '以规范的格式和庄重的称谓开篇，向党组织正式表达入党意愿，奠定全文严肃、诚恳的基调，并清晰阐明申请入党的根本动机与初心。', 'key_points': ['标题：居中写明“入党申请书”。', '称谓：顶格书写“敬爱的党组织”，后加冒号，体现尊重。', '开篇明义：直接、郑重地提出“我志愿加入中国共产党”的核心申请。', '阐述根本动机：简要说明申请入党是源于对党的性质、宗旨、最终目标和光辉历程的认同与向往。', '表明态度：表达提交申请书是经过郑重考虑，并准备接受组织考验的严肃决定。'], 'depend_ids': []}, {'id': 's2', 'sub_goal': '系统阐述对党的理性认识与情感认同，展示申请人对党的基本理论、历史、宗旨和使命的深刻理解，体现政治理论素养，并确保与当前最新的官方表述保持一致。', 'key_points': ['党的性质与地位：阐述对中国共产党作为中国工人阶级、中国人民和中华民族先锋队，中国特色社会主义事业领导核心的认识。', '党的指导思想：论述对马克思列宁主义、毛泽东思想、邓小平理论、“三个代表”重要思想、科学发展观以及新时代中国特色社会主义思想等党的创新理论作为行动指南的理解与信仰。', '党的历史与成就：结合党史、新中国史、改革开放史、社会主义发展史，说明党带领人民取得的伟大成就，坚定对党的信心。', '党的宗旨与初心：深刻理解“全心全意为人民服务”的根本宗旨，以及为中国人民谋幸福、为中华民族谋复兴的初心使命。', '党的最终目标：表明对党的最高理想和最终目标是实现共产主义的认知与追求。'], 'depend_ids': ['s1']}, {'id': 's3', 'sub_goal': '结合个人成长经历、学习工作实践和思想演变过程，具体、真实地剖析个人的入党动机，展现思想觉悟从感性认同到理性追求的升华轨迹，体现动机的纯正性。', 'key_points': ['思想启蒙：描述早期接受的教育、家庭影响、榜样人物（如革命先烈、优秀党员）对个人思想的启蒙。', '认知深化：阐述在学习和生活中（如学校政治课、社会观察、重大事件）对党的理论和政策不断加深理解的过程。', '实践触动：分享在个人学习、工作、社会活动或关键时刻，亲眼所见、亲身经历的党组织和党员发挥先锋模范作用的实例，及其带来的思想触动。', '动机升华：说明从感性认同到理性追求，最终将个人理想融入党和人民事业，决心为共产主义奋斗终身的思想转变与升华。', '（可选）从历史和实践角度，阐明只有中国共产党才能领导中国走向繁荣富强，坚定道路自信、理论自信、制度自信、文化自信。'], 'depend_ids': ['s2']}, {'id': 's4', 'sub_goal': '向党组织全面、客观地汇报个人在思想、学习、工作、作风等方面的现实表现，系统对照党员标准进行诚恳的自我剖析，清晰展示自身与党员要求的符合情况与具体差距。', 'key_points': ['思想政治学习：汇报学习党的理论、路线、方针、政策的情况，以及树立“四个意识”、坚定“四个自信”、做到“两个维护”等方面的具体表现和收获。', '学习/工作表现：结合本职（如学生学业、职工工作），汇报在态度、成绩、贡献、创新等方面的具体事例和成果。', '作风与纪律：汇报在遵守纪律、联系群众、艰苦奋斗、道德品行等方面的表现。', '对照党员标准：系统对照《中国共产党章程》规定的党员义务和条件（如认真学习党的理论、贯彻执行党的路线、坚持党和人民利益高于一切、遵守纪律、维护团结、开展批评与自我批评、联系群众、发扬新风尚等），逐一检视自身的符合情况与差距。', '自我剖析与缺点认识：在对照基础上，诚恳地查找自身在政治理论深度、实践能力、批评与自我批评等方面存在的具体不足和差距。', '剖析原因：深刻分析缺点产生的主观原因，体现自我反思的深度。'], 'depend_ids': ['s3']}, {'id': 's5', 'sub_goal': '针对自身不足，向党组织郑重提出今后的努力方向、改进措施和具体行动计划，并表达接受组织培养、教育和考验的坚定决心。', 'key_points': ['强化理论武装：制定持续深入学习党的创新理论、提高政治站位的具体计划。', '践行党的宗旨：明确如何在实践中更自觉地服务群众、奉献社会的行动方向。', '立足岗位建功：提出在本职岗位上争创佳绩、发挥先锋模范作用的具体目标。', '改进缺点措施：针对自我剖析的不足，提出切实可行的改进步骤和方法。', '接受组织考验：表达无论是否被批准，都将以党员标准要求自己，积极参与组织活动，虚心接受批评教育，经受长期考验的决心。'], 'depend_ids': ['s4']}, {'id': 's6', 'sub_goal': '以庄重的格式结尾，再次明确表达入党意愿和服从组织决定的诚恳态度，完成申请书的完整结构。', 'key_points': ['再次恳请：重申“我志愿加入中国共产党”的强烈愿望，请求党组织审查。', '郑重承诺：表示如果被批准，将如何履行党员义务，珍惜党员身份；如果未被批准，将如何查找不足，继续努力争取。', '表态用语：使用“请党组织在实践中考验我”等规范表述。', '结尾格式：以“此致 敬礼！”等敬语结尾。', '署名与日期：在结尾右下角分行写明申请人姓名和申请日期（年月日）。'], 'depend_ids': ['s1', 's5']}]}

brief = {'raise_error': '', 'main_goal': '撰写一份真诚、规范、体现申请人思想觉悟和入党决心的正式申请书，核心目的是向党组织清晰表达入党意愿、汇报个人思想学习情况、展示对党的认识与忠诚，并请求组织考察与批准。', 'writer': {'学历和认知水平': '申请人通常为具备一定政治理论基础的成年人，认知水平应能理解党的基本理论、纲领和章程。', '语言风格': '正式、庄重、诚恳、朴实。需使用敬语（如“敬爱的党组织”），表达应严肃认真，情感真挚但不过分夸张。', '写作规范': ['1. 格式规范：必须包含标题、称谓、正文、结尾、署名和日期等固定格式要素。', '2. 内容递进：通常按“对党的认识与入党动机 -> 个人情况汇报与自我剖析 -> 今后决心与承诺”的逻辑顺序展开。', '3. 态度诚恳：避免空话套话堆砌，需结合个人真实经历和思想变化来阐述。', '4. 用词准确：正确使用党的理论术语和政治表述，如“党的宗旨”、“先锋模范作用”、“四个意识”等，确保政治表述严谨无误。', '5. 避免主观臆断：对党的评价和个人优缺点的分析应客观求实，符合党章要求。']}, 'target_reader': {'受众身份与认知水平': '党组织（党支部或党委）的负责人及成员，为政治理论水平高、党性原则强的专业人士。', '专业度与表达门槛': '文章需体现政治严肃性，内容必须符合党章和当前政治话语体系，表达需清晰、立场需坚定。', '受众痛点与需求': ['1. 需要高效判断申请人的入党动机是否纯正、对党的认识是否深刻。', '2. 需要评估申请人的思想觉悟、政治素养、现实表现与党员标准的契合度。', '3. 需要看到申请人真诚的自我剖析和改进决心，而非简单抄袭模板。', '4. 需要确认申请书格式规范、态度端正，体现对党组织的尊重。']}, 'success_criteria': {'量化与质性标准': ['1. 结构完整：必须包含所有规定格式模块，顺序正确。', '2. 逻辑清晰：各部分内容衔接自然，思想演进有逻辑性。', '3. 字数适宜：正文部分通常建议在1500-3000字之间，需内容充实、言之有物。', '4. 政治严谨性：所有关于党的理论、历史的表述必须准确无误，与现行官方表述一致。', '5. 真诚度：能清晰感受到申请人的真实情感、个人经历与思考，而非模板化敷衍。', '6. 规范性：语言通顺，格式工整，无错别字和语法错误。']}}


if __name__ == "__main__":
    dag = DAG()
    print(dag.build_plan_dag(outline, brief))
    for node_id, node in dag.nodes.items():
        print(f"节点 {node_id}: {node.title}")
        print(f"任务 {node_id}: {node.task}")
        print(f"依赖: {node.dependencies}")
    dag.calculate_layers()
    dag.print_layer_info()
    print(dag.get_nodes_by_layer())