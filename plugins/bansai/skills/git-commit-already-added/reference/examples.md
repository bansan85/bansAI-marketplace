# Commit message examples

## Good: two concepts, numbered

```
feat(auth): refresh tokens and bump CI image

(1/2) Sessions no longer end abruptly after an hour: the client
now refreshes its token in the background before expiry, and
falls back to a normal re-login if the refresh is rejected.

(2/2) The CI image moves to Node 22, which the refresh timer
needs for its use of AbortSignal.timeout.
```

## Good: one concept, with a context paragraph

```
Fix stale cache after a config reload

Reloading the configuration rebuilt the resolver but left the
previous entries in the lookup cache, so requests kept being
routed with the old rules until the process restarted.

Invalidate the lookup cache as part of the reload, so a reload
takes effect on the next request instead of the next restart.
```

## Good: bug fix, bug paragraph then fix paragraph

```
Fix cache never filled by const getters

The accessors are declared const and were meant to memoize their
result on first call, but the cache member is not mutable, so a
const member function cannot assign to it. Every accessor ended
up recomputing its value on each call.

Declare the cache member mutable, so the const accessors can
fill it on first use. Logical constness is preserved: the value
an accessor returns is unchanged, only the first call is slow.
```

## Good: breaking change under Conventional Commits

```
fix(api)!: correct retreive_config spelling

The public entry point was exported misspelled as
retreive_config. It is now retrieve_config, with the same
signature and the same behaviour; the old name is gone rather
than kept as an alias.

BREAKING CHANGE: retreive_config() no longer exists. Call
  retrieve_config() instead. The arguments and the return type
  are unchanged, so migrating is a rename.
```

## Bad: the fix paragraph repeats the bug, negated

```
Fall back to querying each commit's metadata individually when
the batched git show fails, so one unreadable commit no longer
wipes out the metadata for the rest of the batch. Catch the same
failure when fetching an object's content for preview, and show
a placeholder message instead of letting the exception propagate.
```

"so one unreadable commit no longer wipes out…" and "instead of
letting the exception propagate" only negate the bug paragraph. Cut:

```
Fall back to querying each commit's metadata individually when
the batched git show fails. Catch the same failure when fetching
an object's content for preview, and show a placeholder message.
```

## Bad: the context paragraph invents a reason

User request: "Split FEA-037 in two. FEA-037 must contain ONLY the
low-temperature acquisition and FEA-041 ONLY the high-temperature
one."

```
Each end of the operating temperature range needs the whole bench
brought to its own ambient temperature, and the two runs are
qualified on separate days.
```

The user never said that. Cut the guess, then keep only what was
stated, if it adds to the title: "FEA-037 keeps ONLY the
low-temperature acquisition and the new FEA-041 ONLY the
high-temperature one."

## Bad: invents facts the diff does not hold

```
The problem was found during a code review. It is probably the
cause of the latency spikes reported last month, and lookups
should now be about twice as fast. We first considered dropping
the cache, then adding a TTL, before settling on invalidation.

Closes #482
```

Where it was found is process narration; the cause and the speed-up
were never measured; rejected alternatives are banned; nobody gave
issue 482.
