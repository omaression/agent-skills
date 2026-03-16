# Shared Contracts

## Judge output contract (base)

Judge-plan must emit:
1. Selected architecture
2. Why it won
3. Project/file structure
4. Implementation order
5. Branch plan (name, scope boundary)
6. Test plan
7. PR/CI test gates
8. Simplification targets
9. Done criteria

## Judge output contract (buildx extension)

For `buildx:`, also include:
1. Risk list
2. Likely failure modes
3. Review checklist

## Simplify contract

Must:
- Remove dead code
- Remove speculative abstractions
- Remove duplication
- Remove over-engineered interfaces
- Prefer fewer files when clarity is preserved

Must not:
- Rewrite architecture
- Add abstractions
- Expand scope
