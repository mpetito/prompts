# Branch context: users/dev/rate-limit-login

Base: main. Work item: AB#2210 ("Lock out brute-force login attempts").

## git log main..HEAD --oneline

f3a9c1e test(auth): cover lockout window and reset on success
b7d02aa feat(auth): add sliding-window login rate limiter
41e8c3d chore(config): add RateLimit section to appsettings

## git diff main...HEAD --stat

 src/Api/Auth/LoginRateLimiter.cs        | 84 +++++++++++++++++++++
 src/Api/Auth/LoginController.cs         | 19 ++++-
 src/Api/Auth/ILoginRateLimiter.cs       | 11 +++
 src/Api/Program.cs                      |  3 +
 src/Api/appsettings.json                |  5 ++
 tests/Api.Tests/Auth/LoginRateLimiterTests.cs | 97 ++++++++++++++++++++++++
 6 files changed, 216 insertions(+), 3 deletions(-)

## Key diff excerpts

LoginRateLimiter.cs (new): sliding window keyed by normalised email + client IP.
After `MaxAttempts` (default 5) failures inside `Window` (default 15 minutes) the
limiter returns `Locked` with the remaining seconds. A successful login clears the
key. Storage is `IMemoryCache`, so counts are per-instance and reset on restart.

LoginController.cs: calls the limiter before password verification. A locked
request returns 429 with a `Retry-After` header and never reaches the password
check, so a locked account cannot be probed for "wrong password" vs "no such user".

Program.cs: registers `ILoginRateLimiter` as a singleton and binds `RateLimit`
options from configuration.

appsettings.json: adds `"RateLimit": { "MaxAttempts": 5, "WindowMinutes": 15 }`.

## Validation run on the branch

$ dotnet test tests/Api.Tests
Passed!  - Failed:     0, Passed:    12, Skipped:     0, Total:    12, Duration: 1.4 s

$ dotnet build src/Api -warnaserror
Build succeeded. 0 Warning(s) 0 Error(s)

Not run: the Playwright login e2e suite (needs the staging identity provider),
and nothing has been deployed.
