# FISEVI Web Scrapping Project

This app does web scrapping on *[http://fisevi.com/](http://fisevi.com/)* with
the only aim of being updated about new positions as a researcher in different
health associations in Sevilla.

## Instructions

1. Update RECEIVERS variable in *lib/globals.py* with the mails of the persons
you want to be up to date.

2. Set the [SMTP Client](https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol) (Outlook, Gmail, etc.) associated to the mail account you are using to send the 
message. **SUGGESTION**: I had privacy problems with Gmail so you better use 
Outlook.

3. Create a file *credentials.txt* with the following content
{"User":\<Sender mail account\>, "Password":\<Sender mail password\>}. This file, obviously, must be git ignored.

## Mail sample
