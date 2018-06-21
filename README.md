# MAGBot - Do ALL the things!

This is the collection of custom [Errbot](http://errbot.io) plugins that MAGFest uses to run our Slack ChatOps.

## Getting Started

#### Test Slack Environment
* If you have an `@magfest.org` email address, you can [create an account](https://magfest-test.slack.com/signup) on our [test Slack workspace](https://magfest-test.slack.com)
* If you don't have an `@magfest.org` email address, you can request an invite to our test workspace in the #devops channel on [Slack](https://magfest.slack.com)

#### Test Bot Account
* On the [Custom Integrations](https://magfest-test.slack.com/apps/manage/custom-integrations) page, click on the "Bots" integration
* On the "Bots" page, click the "Add Configuration" button
* Give your bot a recognizable username, like "magbot-yourusername"
* Make a note of your bot's username and API token

#### Local Dev Environment
* Install [docker](https://www.docker.com)
* Clone the magbot repository:
```
git clone https://github.com/magfest/magbot.git && cd magbot
```
* Run magbot using the `run-dev.sh` script with your bot's username and API token:
```
./run-dev.sh magbot-username xoxb-XXXXXXXXXXXX
```

#### Developing
* You can now interact with your local magbot on the [test Slack workspace](https://magfest-test.slack.com)
* In a DM with your magbot, type `!help` to get a list of commands
* As you make changes in the local copy of your plugin, you can type `!plugin reload MyPluginName` to make your changes live
