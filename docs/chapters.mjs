import { metadata, englishGroups } from './metadata.mjs'
// The only chapter registry. Article bodies remain in their original directories.
export const groups = [
  { id: 'foundations', label: '基础与优化', note: '理解一次策略更新', number: '01' },
  { id: 'distillation', label: '蒸馏与自学习', note: '把反馈变成学习信号', number: '02' },
  { id: 'agents', label: '工具与环境', note: '让模型走进交互环境', number: '03' },
  { id: 'frontiers', label: '多模态与前沿', note: '探索更长、更复杂的任务', number: '04' },
]

export const chapters = [
  { id: 'loss-functions', number: '00', title: 'Loss Functions', subtitle: '从直觉理解强化学习损失', group: 'foundations', source: '00-loss-function/readme.md', description: '从 importance sampling 到 PPO、CISPO，看清每一次策略更新到底在优化什么。', tags: ['入门', '目标函数'] },
  { id: 'grpo', number: '01', title: 'GRPO', subtitle: '从组内比较开始', group: 'foundations', source: '01-grpo/readme.md', start: '01-grpo/start.md', description: '在 GSM8K 上走通采样、奖励与更新，亲手比较三种 loss 的训练行为。', tags: ['GSM8K', '组相对优势'] },
  { id: 'general-opd', number: '02.1', title: 'General OPD', subtitle: '让学生在自己的轨迹上学习', group: 'distillation', source: '02-opd/general-opd/readme.md', description: '用 DeepMath-103K 串起 Student 采样、Teacher 打分与 reverse KL。', tags: ['蒸馏', 'DeepMath'] },
  { id: 'medical-opd', number: '02.2', title: 'Medical OPD', subtitle: '专业能力与通用能力的平衡', group: 'distillation', source: '02-opd/readme.md', start: '02-opd/start.md', description: '从 Medical SFT 出发，实验 SAR-OPD 与 IDT-OPD，观察多任务能力的变化。', tags: ['医疗任务', '多教师'] },
  { id: 'search-r1', number: '03', title: 'Search-R1', subtitle: '学会在思考中搜索', group: 'agents', source: '03-search-r1/readme.md', start: '03-search-r1/start.md', description: '把在线搜索放进 rollout，让模型在多轮检索中学会寻找证据、组织答案。', tags: ['在线搜索', '多轮交互'] },
  { id: 'opsd', number: '04', title: 'OPSD', subtitle: '从自己生成的轨迹中蒸馏', group: 'distillation', source: '04-opsd/readme.md', start: '04-opsd/start.md', description: '固定 step-0 Teacher，在 Student 自采样轨迹上构造蒸馏信号。', tags: ['自蒸馏', '数学推理'] },
  { id: 'retool', number: '05', title: 'ReTool', subtitle: '把 Python 变成推理工具', group: 'agents', source: '05-retool/readme.md', start: '05-retool/start.md', description: '连接本地代码沙箱，复现思考与代码执行交织进行的 Agentic RL。', tags: ['代码沙箱', '工具调用'] },
  { id: 'dapo', number: '06', title: 'DAPO', subtitle: '拆开训练稳定性的四个改进', group: 'foundations', source: '06-dapo/readme.md', start: '06-dapo/start.md', description: '拆解四项核心设计，记录 Dynamic Sampling 在真实训练中的收益与时间成本。', tags: ['动态采样', '训练稳定性'] },
  { id: 'gspo', number: '07', title: 'GSPO', subtitle: '把优化单位提升到序列', group: 'foundations', source: '07-gspo/readme.md', start: '07-gspo/start.md', description: '实现 sequence-level 重要性比率与裁剪，厘清核心 loss 和完整训练的边界。', tags: ['序列级优化', '自定义 Loss'] },
  { id: 'alfworld', number: '08', title: 'ALFWorld', subtitle: '训练一个会做家务的 Agent', group: 'agents', source: '08-alfworld/readme.md', start: '08-alfworld/start.md', description: '在真实 TextWorld 环境里，处理长轨迹、环境反馈与家务任务。', tags: ['具身环境', '长轨迹'] },
  { id: 'vision-grpo', number: '09.1', title: 'Vision GRPO', subtitle: '让强化学习看见图片', group: 'frontiers', source: '09-vision-grpo/readme.md', start: '09-vision-grpo/start.md', description: '在 GeoQA 上接入图像输入，把图文推理与可验证奖励串起来。', tags: ['视觉语言模型', 'GeoQA'] },
  { id: 'tempo', number: '09.2', title: 'TEMPO', subtitle: '用小段轨迹学习长程任务', group: 'frontiers', source: '09-tempo/readme.md', description: '在 ALFWorld 中探索 macro-step 优化与生成式 critic，记录算法级复现的边界。', tags: ['Macro-step', '生成式 Critic'] },
  { id: 'agentopsd', number: '09.3', title: 'AgentOPSD', subtitle: '把信用分配到每一轮交互', group: 'frontiers', source: '09-AgentOPSD/readme.md', start: '09-AgentOPSD/start.md', description: '让带 Skill 的 Self-Teacher 给出 turn-level 信号，分析多轮 Agent 的学习过程。', tags: ['信用分配', 'Self-Teacher'] },
  { id: 'spec-o3', number: '09.4', title: 'Spec-o3', subtitle: '用强化学习寻找天上的星星', group: 'frontiers', source: '09-spec-o3/readme.md', start: '09-spec-o3/start.md', description: '从 SFT 到 GRPO，让模型边看光谱、边思考、边调用工具完成天体候选审核。', tags: ['光谱分析', '多模态工具'] },
]

export const repoUrl = 'https://github.com/KMnO4-zx/agentic-rl-lab'
export const chapterLink = (chapter, locale = 'zh') => `${locale === 'en' ? '/en' : ''}/experiments/${chapter.id}/`
export const localizedChapters = (locale = 'zh') => chapters.map(c => ({ ...c, ...metadata[c.id], ...(locale === 'en' ? metadata[c.id].en : {}) }))
export const localizedGroups = (locale = 'zh') => groups.map(g => ({ ...g, ...(locale === 'en' ? englishGroups[g.id] : {}) }))

// The website supplies its own title treatment; retain all instructional/result figures.
export const articleCovers = {
  grpo: './images/GRPO.png',
  'general-opd': './images/OPD-deepmath.png',
  'medical-opd': './images/OPD-head.png',
  'search-r1': './images/封面.png',
  opsd: './images/head.png',
  retool: './images/封面.png',
  dapo: './images/head.png',
  gspo: './images/封面.png',
  alfworld: './images/封面.png',
  'vision-grpo': './images/vision-grpo.png',
  tempo: './images/封面.png',
  agentopsd: './images/封面.png',
  'spec-o3': './images/封面.png',
}
