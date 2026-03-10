# Wave22 Product Research Sources

## Objective
- Capture current external references that can improve Cockpit as a desktop-first operator room for multi-agent work.

## Source set
1. Material Design 3 - window size classes and adaptive layout
- URL: https://m3.material.io/foundations/layout/applying-layout/window-size-classes
- Why it matters: useful for desktop/tablet split, segmented operator panes, and layout fallback rules.

2. WAI-ARIA Authoring Practices - tabs pattern
- URL: https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
- Why it matters: Cockpit top tabs and room/direct switching need stronger keyboard and focus behavior.

3. WebAIM - contrast and low-vision readability
- URL: https://webaim.org/articles/contrast/
- Why it matters: current shell still risks low-contrast helper copy, pills, and dense room/chat surfaces.

4. Nielsen Norman Group - dashboard and progressive disclosure guidance
- URL: https://www.nngroup.com/articles/dashboards/
- URL: https://www.nngroup.com/articles/progressive-disclosure/
- Why it matters: Cockpit should show dense operator data without flooding the main task path.

5. Anthropic - building effective agents
- URL: https://www.anthropic.com/engineering/building-effective-agents
- Why it matters: room orchestration should privilege visible plans, bounded delegation, and honest degraded behavior.

6. OpenAI - agents guidance and realtime interaction patterns
- URL: https://platform.openai.com/docs/guides/agents
- URL: https://platform.openai.com/docs/guides/realtime
- Why it matters: direct chat vs orchestration room should stay separated, with explicit system state and human override.

## Research takeaways mapped to Cockpit
- `Pixel Home` should be a direct operator lane, not a mixed orchestration surface.
- `Le Conseil` should be the multi-agent coordination room, with visible participant outputs and diagnostics separation.
- Dense context belongs in secondary cards, not in the main composer row.
- Degraded network/LLM state must be explicit and honest, never disguised as success.
- Tablet mode should reduce side-by-side density before it reduces functionality.
