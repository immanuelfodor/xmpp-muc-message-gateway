# XMPP MUC Message Gateway

A simple Docker-based microservice that forwards a JSON object received in an HTTP POST request to an XMPP MUC room ([XEP-0045](https://xmpp.org/extensions/xep-0045.html)) through a `TLSv1.2` client connection using the [SleekXMPP](https://sleekxmpp.readthedocs.io/en/latest/) Python lib. Supports multiple rooms and sender aliases with different associated URLs, e.g, one for Grafana, another for `curl`, and so on. Can convert JSON to YAML for better message readability. Easy installation with `docker-compose`.

## Table of contents <!-- omit in toc -->

- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Build & run](#build--run)
  - [Network topology](#network-topology)
- [Local development / quick test](#local-development--quick-test)
- [Disclaimer](#disclaimer)
- [Contact](#contact)

## Dependencies

- [Docker](https://www.docker.com/)
- [Docker Compose](https://github.com/docker/compose)

Installation on Manjaro Linux:

```bash
sudo pacman -S docker docker-compose

sudo systemctl enable docker
sudo systemctl start docker
```

Of course, you'll also need a MUC-enabled [XMPP server](https://xmpp.org/software/servers.html) up and running with at least one MUC room and two users joined in the same room (the webhook user and _you_). Explaining setting these up is way beyond the scope of this document, so please see the online docs for proper instructions. They say [Prosody](http://prosody.im/) is beginner-friendly.

## Configuration

You can configure the gateway as you like, but you must have at least one valid XMPP user JID, password and an associated `token:room-JID:nick` combo in a `.pyenv` file to make it work.

Create a copy of the example config file provided, and add the parameters according to the example:

```bash
cp .pyenv{.example,}
# edit the .pyenv with your preferred editor
```
```bash
# The user we authenticate with becomes the sender of the message
export JID_FROM_USER="user@host"

# Cleartext password of the above user
export JID_FROM_PASS="my-StroNG-pAssWOrd"

# The webhook token and its associated MUC receives the message from the displayed nick
# Can be a list of valid forward targets by separating every pair with a space
# The same room with different token and nick lets you reuse the same user for multiple services
# You can easily generate a Slack-like new token with running the following in bash:
#   openssl rand -hex 10 | tr [a-z] [A-Z]
export KNOWN_ROOMS="token1:room1@conf.host:nick1 token2:room2@conf.host:nick2 token3:room1@conf.host:nick3"

# The log level of the XMPP lib can be different from the Gunicorn/Flash app
# Defaults to the Docker env setting
export XMPP_LOG_LEVEL="${LOG_LEVEL}"

# Format of the XMPP message. Pretty printed, indented by 2 spaces. Supported values:
#   - json: better portability of the original JSON, unicode characters are converted to \u1231 and such
#   - yaml: better readability, unicode characters are allowed for better readability (avoid \u1231 and such chars in messages)
export MESSAGE_FORMAT="json"
```

## Usage

### Build & run

Build the project, start it in the background, send some example messages, and check the logs:

```bash
sudo docker-compose up --build -d

# Should produce a 404 error if you don't have an 'asdasd' token in your config
# or a null message in your client if you have one as we sent regular form data
curl -X POST \
  http://localhost:10080/post/asdasd \
  -F foo=bar
# {"error":"404 Not Found: Token mismatch"}
# {"success":true} - but null message

# should be forwarded successfully as valid JSON if the token exists
curl -X POST \
  http://localhost:10080/post/MYTOKEN \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Test message",
    "text": "Hello World!"
}'
# {"success":true}

sudo docker-compose logs
```

Anytime you modify anything in the config, you need to rebuild the image and rerun the container using the first command.

**Tip**: Adjust the gateway's log level to higher verbosity with `LOG_LEVEL=debug` in a `docker-compose.override.yml` file.

**Tip**: Use a [`curlrc`](https://ec.haxx.se/cmdline-configfile.html) file to store default config if sending POST requests from Bash:

```bash
cat > $HOME/.curlrc.xmpp <<EOF
url = "http://ip-or-hostname:10080/post/MYTOKEN"
header = "Content-Type: application/json"
EOF

curl -K $HOME/.curlrc.xmpp -d '{"hello":"curlrc"}'
```

When using in a crontab, you might want to replace `$HOME` with the absolute path of the file.

**Tip**: Convert _anything_ to valid JSON with [`jq`](https://stedolan.github.io/jq/) (version `>=1.4`) using the following oneliner:

```bash
cat /etc/hosts | jq -R -s -c 'split("\n")' | curl -K $HOME/.curlrc.xmpp -d @-
```

### Network topology

You can put the gateway behind a reverse proxy preferably with an SSL cert from, e.g., Let's Encrypt. You can also host the XMPP message gateway on the same domain as your XMPP server by using a _subpath configuration_, for example, matching on the `/post/...` part of the URL, see the `push.py` in this repo for details. Of course, adding another _server block_ for a new subdomain is also convenient.

Malicious actors could only send spam notifications if they would know any of your long and random tokens, otherwise, the messages are not routed to a valid XMPP MUC room. However, the following setup is desirable when we don't want to expose it to the open, and it's also easier to achieve.

If you host your message source, XMPP server and this gateway on the same network, you can use local hostnames, DNS or IP addresses to set everything up:
- Add the gateway to the data source (e.g., [Grafana webhook](https://github.com/grafana/grafana/issues/6955#issuecomment-470900383)) with the gateway's local hostname/IP + port e.g., `http://10.0.0.80:10080/post/rANd0m-tOkEN`
- Add the local XMPP user's JID and the local MUC JID to the gateway's config with a local hostname/IP, e.g., `bot@xmpp.server.local` and `hook@conference.xmpp.server.local`

This way the message gateway won't be accessible from the outside, and your message data won't leave the internal network.

The final network topology looks like:

```
                                    +-----------+
                           HTTP     |           |
                       +----------->+  Grafana  |
                       |            |           |
                       |            +-----+-----+
                       |                  |
                       |                  | HTTP
          +------------+--+               v
   HTTPS  |               |        +------+----------+
+---------+ Reverse proxy |        |                 |
          |               |        | Message gateway |
          +------------+--+        |                 |
                       |           +-----------+-----+
                       |                       |
                       |                       | TLS 1.2
                       |                       v
                       | Bosh, Websocket +-----+-------+
                       +---------------->+             |
   TLS 1.2                               | XMPP server |
+--------------------------------------->+             |
                                         +-------------+
```

## Local development / quick test

Step into the gateway's Docker container and run the included `xmpp_client.py`:

```bash
sudo docker-compose exec xmpp-msg-gw sh

python xmpp_client.py
# Usage: xmpp_client.py [options] your message text
#
# Options:
#   -h, --help            show this help message and exit
#   -j JID, --jid=JID     JID to use
#   -n NICK, --nick=NICK  MUC nickname
#   -p PASSWORD, --password=PASSWORD
#                         password to use
#   -r ROOM, --room=ROOM  MUC room to join
#   -v, --verbose         Verbosity to maximum

python xmpp_client.py -j my_user@host -n my_nick -p my_pass -r hook@conference.xmpp.server "cli test"
```

You can send test messages to see it in action, or experiment with the programmable client to implement new features.

## Disclaimer

**This is an experimental project. I do not take responsibility for anything regarding the use or misuse of the contents of this repository.**

Tested with Grafana webhooks and Prosody as an XMPP server, but in theory, it should work with any source capable of sending HTTP POST requests with valid JSON objects (e.g., `curl`).    
The posted JSON object is formatted and indented by 2 spaces, no further processing is being made. The padded object's size is limited by your XMPP server's maximum stanza or body size.    
[OMEMO](https://omemo.top/) is not yet supported in SleekXMPP by default, but there is an interesting project out there which worth exploring: [sleekxmpp-omemo-plugin](https://gitlab.com/ecartman/sleekxmpp-omemo-plugin)    
`pyasn1` and `pyasn1-modules` are not included in the `requirements.txt` as optional SleekXMPP dependencies, so the SSL cert verification and expiration check won't work, see [this issue](https://github.com/fritzy/SleekXMPP/issues/477) for further info.

## Contact

Immánuel Fodor    
[fodor.it](https://fodor.it/xmppmsggwit) | [Linkedin](https://fodor.it/xmppmsggwin)
