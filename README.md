# Tracker

[@tagtrackbot](https://t.me/tagtrackbot)  
Tracks bugs and feature suggestion messages on trello boards. Currently operational in the [@macswift](https://t.me/macswift) MacOS Swift beta chat.

### Functions:
- creates and sorts Trello cards in the presence of certain tags in a message (more info below).
- changes the status of the cards based on the replies of admins/developers (more info below).
- downloads and adds any attachements (including photo albums) from the message to its repsective trello card (max limit **10MB** per file).
- finds and specifies the version of the application in the trello card (using regex).
- also adds the original t.me message link within the chat to the trello card.

### Tags:
- `#bug` - bugs in the logic of the application.
- `#visual` - interface bugs.
- `#suggestion`, `#feature` - new functionality suggestions.

### Sorting:
1) `#bug` & `#visual` go to one trello board [e.g. [Bugs & Visual](https://trello.com/b/P4sepLgm/bugs-visual)]. Each tag has it's separate trello list.
2) #suggestion & #feature go to a separate board [ e.g. [Feature Requests](https://trello.com/b/ag5JfYS7/feature-requests)].


### Admins / Developers:
- can reply to the tagged messages with `fixed`, `done`, among other things, which moves the associated card to the `Completed` list on their respective trello boards.
- can also reply with `no`, `not a bug`, `reject` etc. and the card is moved into the `Rejected` list.