<template>
  <div class="loop-figure">
    <div class="figure-bar"><span><i /> INSIDE THE TRAINING LOOP</span><span>FIG. 01</span></div>
    <svg viewBox="0 0 520 350" role="img" aria-labelledby="loop-title loop-desc">
      <title id="loop-title">强化学习训练循环示意</title>
      <desc id="loop-desc">策略模型采样多条轨迹，环境给出奖励，计算优势并更新策略。示意图不代表真实实验指标。</desc>
      <defs>
        <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="currentColor" opacity=".12" /></pattern>
        <marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#709483" /></marker>
      </defs>
      <rect width="520" height="350" fill="url(#dots)" />
      <g fill="none" stroke="#95aa9c" stroke-width="1.5" marker-end="url(#arrowhead)">
        <path d="M162 100H206Q221 100 221 80V65H260" />
        <path d="M162 100H260" />
        <path d="M162 100H206Q221 100 221 120V135H260" />
        <path d="M366 65H390Q405 65 405 87V189" />
        <path d="M366 100H405" /><path d="M366 135H405" />
        <path d="M337 233H190" />
        <path d="M115 202V143" />
      </g>
      <path class="loop-pulse" d="M115 143V100H210Q221 100 221 80V65H405V233H115V143" fill="none" stroke="#346d57" stroke-width="2" stroke-dasharray="6 610" />
      <rect class="loop-policy" x="48" y="60" width="116" height="84" rx="13" />
      <text x="68" y="86" class="loop-mono loop-inverse" font-size="10">POLICY</text>
      <text x="68" y="116" class="loop-inverse" font-size="23" font-weight="600">π<tspan dy="4" font-size="13">θ</tspan><tspan dy="-4" dx="20" font-size="15">Agent</tspan></text>
      <g class="loop-rollouts">
        <rect x="263" y="49" width="103" height="30" rx="7" /><rect x="263" y="85" width="103" height="30" rx="7" /><rect x="263" y="121" width="103" height="30" rx="7" />
      </g>
      <g class="loop-tokens" fill="#9bac9b">
        <path d="M277 60h8v8h-8zM290 60h8v8h-8zM303 60h8v8h-8zM316 60h8v8h-8zM329 60h8v8h-8z" />
        <path d="M277 96h8v8h-8zM290 96h8v8h-8zM303 96h8v8h-8zM316 96h8v8h-8z" />
        <path d="M277 132h8v8h-8zM290 132h8v8h-8zM303 132h8v8h-8zM316 132h8v8h-8zM329 132h8v8h-8zM342 132h8v8h-8z" />
      </g>
      <text x="271" y="30" class="loop-mono" font-size="10">GROUP ROLLOUTS</text>
      <text x="425" y="165" class="loop-mono" font-size="10" transform="rotate(90 425 165)">FEEDBACK</text>
      <rect class="loop-update" x="47" y="204" width="143" height="58" rx="11" />
      <text x="64" y="227" class="loop-mono" font-size="9">OPTIMIZE</text><text x="64" y="247" font-size="14" font-weight="600">更新策略 <tspan dx="8" class="loop-mono">θ → θ′</tspan></text>
      <rect class="loop-reward" x="337" y="204" width="128" height="58" rx="11" />
      <text x="354" y="226" class="loop-mono reward-label" font-size="9">ENVIRONMENT</text><text x="354" y="247" class="reward-label" font-size="14" font-weight="600">评估与奖励</text>
      <text x="223" y="220" class="loop-mono" font-size="10">ADVANTAGE</text>
      <text x="260" y="317" text-anchor="middle" class="loop-caption" font-size="12">采样 · 交互 · 反馈 · 更新</text>
    </svg>
    <div class="figure-foot"><span>一个循环，串起论文与代码。</span><span>流程示意 ↗</span></div>
  </div>
</template>
