# Issue tracker

Issues live in GitHub Issues on `django-mvp/shared`, managed via the `gh` CLI.

- One issue per problem or proposal; changes to the family standard get an issue first so
  the downstream impact is stated before work starts.
- Every issue that changes a reusable workflow, a dependency bundle, or a template should
  name the affected downstream surface (workflow inputs, extras, template file) in the body.
- Dependabot PRs are not issues; they flow through the auto-merge lane gated by the
  validation checks.
