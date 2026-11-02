# Talking points (about 4.5 minutes)

**Slide 1 (10 s).** "I evaluated the file transfer service with three experiments: packet loss, file size, and load."

**Slide 2 (40 s).** Walk the diagram left to right. Stress two facts: files go as 64-byte UDP chunks, and every download takes at least 2 s because the client waits for 2 s of silence. "I changed one variable per experiment and wrote predictions before running."

**Slide 3 (45 s).** "If retries worked like the first send, 20% loss should still give 94% success for 64 KB. I got zero. At 10% loss, 1 MB never worked. Successful downloads went from 2.4 s to 11 s because each retry round costs at least 2 s."

**Slide 4 (35 s).** "With no loss configured, small files were perfect, but 256 KB and up mostly failed. The over-limit file gives a misleading 504 instead of 'file too large'."

**Slide 5 (45 s). Key slide.** "The code explains both. The burst loses some chunks, the client sends one retry per missing chunk all at once, the backend's 32-slot queue drops most of them, and each retry that gets through re-downloads the whole file from S3 to send 64 bytes. The reliability mechanism amplifies load when the system is struggling."

**Slide 6 (45 s).** "I predicted 2 requests/s per gateway task: 4 in-flight slots over 2 s. At 15 users, throughput went flat at exactly 4.0 with 2 tasks. At 40 users, 28% got 503s. Scaling came 2 minutes late, and the second scale-out came after the load was gone. The backend never scaled because CPU stayed low."

**Slide 7 (30 s).** Read the four findings, then the top fix: batch chunk IDs in one RETY and cache the file.

**Slide 8 (15 s).** "Small samples and short load steps, but the trends were large and consistent."

## Likely follow-up questions
- *Why not just raise the retry count?* More rounds still each lose most RETYs to the 32-slot queue, and each costs 2 s plus full-file S3 reads; it adds latency without fixing the cause.
- *Why did 0% loss still fail?* Real loss from huge bursts plus the retry overload; configured loss is not the only loss.
- *How would you scale the backend instead?* On a load signal such as dropped-message count or queue depth published as a custom CloudWatch metric, not CPU.
- *Why is the gateway at 2 req/s per task?* Little's law: throughput = concurrency / latency = 4 / ~2 s.
