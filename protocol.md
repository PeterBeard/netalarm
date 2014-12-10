Network commands
----------------

**Client -> Server**
* B *NAME* -- Subscribe to alarm *NAME*
* U *NAME* -- Unsubscribe from alarm *NAME*
* Following server A command
  * S *NAME* -- Alarm *NAME* succeeded
  * F *NAME* -- Alarm *NAME* failed

**Server -> Client**
* A *NAME* -- Trigger alarm *NAME*
* Following client *B* command
  * S *NAME* -- Subscription to *NAME* succeeded
  * FN *NAME* -- Subscription to *NAME* failed; it doesn't exist
  * FB *NAME* -- Subscription to *NAME* failed; already subscribed
* Following client *U* command
  * S *NAME* -- Unsubscription from *NAME* succeeded
  * FN *NAME* -- Unsubscription from *NAME* failed; it doesn't exist
  * FB *NAME* -- Unsubscription from *NAME* failed; already subscribed

