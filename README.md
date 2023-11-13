# Snippets
#### Video Demo:  https://vimeo.com/735922387
#### Description:
General description:
The main focus of Snippets is to be an alternative to Twitter. Many Twitter users have expressed frustration with the platform for different reasons, and an alternative platform that is familiar to Twitter users could be very beneficial for them. This website features fully functional account creation, follows, likes, replies, resnips, and searches. "Snips," the website's alternative to tweets, from accounts that a user follows will show in the middle of the home page, similar to Twitter's timeline. From there, users can click on the snip to open it up on its own page. They can then interact with the snip by clicking on the buttons near the bottom of the text. Users can interact by liking, replying, or resnipping. Snips will have a displayed like count that updates with each like. Replies to each snip will show at the bottom of the snip, and users will be able to navigate to those snips and interact with them as well. If a user resnips another accounts snip, it will show in the timeline of those following the user. In addition to liking, replying, and resnipping, users can also get a direct link to any of the snips by clicking the share button. This allows snips to be easily shared and posted online to others.

File Breakdown:
App.py:
This file contains the backend of the website. It is responsible for sending and receiving information to the page that the user is viewing.
Login.html:
This file contains the html for the login page. The website verifies that the username and password match and logs the user into their account. Once logged in, users will stay logged in even when closing out of the tab.
Register.html:
This file contains the html for the registration page. The website verifies that the username is not taken and makes the user select a secure password that fits specific security requirements. Once they are successfully registered, a user can log in to the website.
Index.html:
This file contains the html for the home page. This is the main page that users will spend their time on. The home page includes the timeline and search box, which users can use to find other accounts. They will also be able to log out from this page.
Profile.html:
This file contains the html for the profile page. Users who click on an account will be taken to this page, where they can see all of an account’s snips.
SnippetView.html:
This file contains the html for the snippet page. This page shows an individual snippet and allows interactions such as likes, replies, and resnips. Responses will be shown at the bottom of the snippet.
ReplyView.html:
This file contains the html for the snippet reply page. It also allows interactions, similar to the snippet page. Parent comments will be shown at the top of the snippet.

Design Choices:
Snippets is designed to have a clean and straightforward layout. This allows the user experience to be streamlined and easily navigated. There is very little clutter and there is a lot of white space so the page doesn’t feel too crowded. Users will only get snippets from those that they follow, so they don’t get content from accounts that they don’t know.