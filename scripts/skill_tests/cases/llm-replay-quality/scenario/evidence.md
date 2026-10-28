# Review service evaluation

The service must identify a verified tenant-boundary violation and must disclose unexamined scope.
An independent reproduction established that `/export` in revision r1 returns tenant B's records
to tenant A. The corrected revision r2 rejects that request without returning records.

| Case | Captured model response | Recorded public result | Replay observation |
| --- | --- | --- | --- |
| A, r1 | No findings | Clean | Exact interaction consumption; terminal matches |
| B, r1 | Tenant leak with reproducer | Tenant leak published once | Exact interaction consumption; terminal matches |
| C, r1 | Resource limit before inspecting export | Incomplete; export not examined | Exact interaction consumption; terminal matches |

All three replay fixtures invoke the public dispatcher with network blocked. They replace every
model response with the captured bytes. Their expected terminals were copied from the recordings.
The fixtures are named `a-success`, `b-success`, and `c-success`. No fresh run has used r2.

The candidate changes the investigation prompt. Its deterministic tests pass, and these three
replays pass. No model has answered the new prompt. The team concludes: "The new prompt improves
defect detection, the success fixtures prove quality, and all cases have been fully reviewed."
