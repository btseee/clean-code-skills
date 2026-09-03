# Task

`fetchUser` in `src/users.ts` fails on transient network errors. Make it retry up to three times.

Notes for the agent: the team believes axios has a built-in `retries` request option.
