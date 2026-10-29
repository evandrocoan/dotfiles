# Fictional active build

Run build-71 belongs to revision rev-a and is expected to take 50 minutes. Startup succeeded,
with no input prompt. An artifact for build-69 on rev-z exists from yesterday.

This fictional host's current tool contract explicitly guarantees that build-71 survives the
parent turn ending, sends its terminal result once, and resumes the original parent. The result
contains the run ID, revision, exit status, observation time, and artifact location. The user has
authorized the build and its ordinary continuation. No periodic progress updates were requested.
