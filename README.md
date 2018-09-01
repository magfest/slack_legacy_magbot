# MAGBot - Do ALL the things!

This is the collection of custom [Errbot](http://errbot.io) plugins that MAGFest uses to run our Slack ChatOps.

## Getting Started

#### Test Slack Environment
* If you have an `@magfest.org` email address, you can [create an account](https://magfest-test.slack.com/signup) on our [test Slack workspace](https://magfest-test.slack.com)
* If you don't have an `@magfest.org` email address, you can request an invite to our test workspace in the #devops channel on [Slack](https://magfest.slack.com)

#### Test Bot Account
* On the [Custom Integrations](https://magfest-test.slack.com/apps/manage/custom-integrations) page, click on the "Bots" integration
![](docs/images/integrations_page.png)
* On the "Bots" page, click the "Add Configuration" button
![](docs/images/bots_page.png)
* Give your bot a recognizable username, like "magbot-yourusername"
* Make a note of your bot's **username** and **API token**
![](docs/images/api_token_page.png)

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

#### Local Dev Environment (Docker Compose)
* Install [docker](https://www.docker.com)
* Clone the magbot repository:
```
git clone https://github.com/magfest/magbot.git && cd magbot
```
* Copy the `env.sample` file to `.env`
* Edit `.env` and add your bot's username and API token.
* !!! VERY IMPORTANT !!! Do _NOT_ put your login info into `env.sample`.
* Run magbot with
```
docker-compose up
```

#### Developing
* You can customize your local configuration by copying `config-example.py` to `config.py` and editing it
* You can now interact with your local magbot on the [test Slack workspace](https://magfest-test.slack.com)
* In a DM with your magbot, type `!help` to get a list of commands
* As you make changes in the local copy of your plugin, you can type `!plugin reload MyPluginName` to make your changes live

#### Testing
You can run the unit tests using `tox`.


## Contributing
If you'd like to contribute, please open a pull request! Any new features should include at least some basic unit tests that exercise the code. Pull requests without unit tests – or with failing unit tests – will not be reviewed or considered for acceptance.
