Network commands
----------------

**Client -> Server**
* B *NAME* -- Subscribe to alarm *NAME*
* S *NAME* -- Alarm *NAME* succeeded
* F *NAME* -- Alarm *NAME* failed

**Server -> Client**
* A *NAME* -- Trigger alarm *NAME*
* S *NAME* -- Subscription to *NAME* succeeded
* FN *NAME* -- Subscription to *NAME* failed; it doesn't exist
* FB *NAME* -- Subscription to *NAME* failed; already subscribed

