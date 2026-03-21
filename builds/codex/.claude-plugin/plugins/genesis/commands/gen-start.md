# /gen-start — State-Driven Entry Point

Run the engine and let it select the next unconverged edge.

```bash
PYTHONPATH=.genesis python -m genesis start --workspace . [--auto]
```

Route on the engine exit code:

- `0`: converged / nothing to do
- `2`: F_P dispatched
- `3`: F_H gate pending
- `4`: F_D still failing
- `5`: loop limit reached
