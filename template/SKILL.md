---
name: example-skill
description: Starter template for a nanolama skill. Replace this whole description with a third-person sentence that says WHAT the skill does (with concrete stack keywords) and, after "Use when", the exact triggers, verbatim user phrases, and file types that should activate it. Optionally end with "Not for ..." to hand an adjacent area to a sibling skill. Keep it under 1024 characters. Use when you are creating a new skill and copying this folder as a starting point.
---

# Example Skill

> Copy this folder to `skills/<your-name>/`, rename it, rewrite every section,
> then add the skill to `scripts/catalog.yaml`. Run `python scripts/validate_skills.py`.
> See the `skill-authoring` skill for the full contract.

## When to use
One or two lines naming the concrete situation this skill applies to.

## Pattern
The core principle in 1-2 sentences — the invariant to hold, stated so it is
true in any repo on this stack, not just one codebase.

## Steps / idioms
1. First concrete step.
2. Second step, with one short commented example (keep inline code under ~40 lines):

   ```python
   # Minimal, correct, copy-adaptable — not a full app.
   queryset = Model.objects.filter(entreprise=request.user.entreprise)
   ```

3. Third step.

## Adapt to your repo
What a reader must rename or confirm before using this: model names, the tenant
accessor path, settings keys, package versions. nanolama is portable — never
assume one project's exact file paths.

## Gotchas
- The sharp edge that bites people, and how to avoid it.

## See also
- `skill-authoring`
