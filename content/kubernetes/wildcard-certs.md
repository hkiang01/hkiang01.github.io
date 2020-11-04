---
title: "Wildcard certs"
date: 2020-10-17T15:58:10-05:00
weight: 2
draft: false
---

This is NOT representative of what I do at work (mostly for my home hobby cluster).

Once you have [NGINX](https://docs.nginx.com/nginx-ingress-controller/installation/installation-with-helm/) set up, each of your services can sit behind an [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) with a host resembling something close to *myservice.mydomain.com*.
That's great and all, but you'll find that your connections aren't secured until you configure [TLS](https://kubernetes.io/docs/concepts/services-networking/ingress/#tls).

## Some understanding

You'll need to pass a [DNS-01 challenge](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge).
The challenge itself is run by servers from a certificate authority (CA) such as [Let's Encrypt](https://letsencrypt.org/).
Those servers expect your web server to be reachable from whatever IP address your domain points to.


## Clusters with a public IP

It's fairly straightforward to secure your services via [cert-manager](https://cert-manager.io/docs/tutorials/acme/ingress/) as the Let's Encrypt servers will be able to reach your node clusters (which play the role of your web server).

## Clusters without a public IP

Solutions like cert-manager won't work out of the box here.
Essentially you'll need to stand up a web service apart from your cluster that has a static IP for the sole purpose of getting the pem certs requried to generate your [TLS Secrets](https://kubernetes.github.io/ingress-nginx/user-guide/tls/#tls-secrets).
AWS, Google Cloud, etc., are able to provide here.

Note: the following instructions are tested on a server running Ubuntu 20.04:

1. Set up a server with a publicly accessible static IP address either in the cloud or some other hosting provider you trust.

2. Create an A record pointing to its static IP.
Below is an example:

![sample_dns](https://i.imgur.com/CYaRu8Z.png)

Replace the IP address Value with your server's static IP.

3. Install the following in the same server:
- [certbot](https://certbot.eff.org/docs/install.html)
  - used to get tls cert from [Let's Encrypt](https://letsencrypt.org/)
- [nginx](https://ubuntu.com/tutorials/install-and-configure-nginx#2-installing-nginx)
  - used as the installer [plugin](https://certbot.eff.org/docs/using.html#nginx) when [combining plugins](https://certbot.eff.org/docs/using.html?highlight=manual#combining-plugins)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
  - used to locally render the secret to copy over to our private cluster

4. In your publicly available server, create an index.html file that will display something.

```bash
# server with publicly available static ip
cd /var/www
sudo mkdir tutorial
cd tutorial
sudo "${EDITOR:-vi}" index.html
```

```html
<!-- index.html -->
<!-- This is what the nginx server will return -->
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Hello, Nginx!</title>
</head>
<body>
    <h1>Hello, Nginx!</h1>
    <p>We have just configured our Nginx web server on Ubuntu Server!</p>
</body>
</html>
```

5. In your publicly available server, configure NGINX as shown below:

```bash
# server with publicly available static ip
cd /etc/nginx/sites-enabled
sudo "${EDITOR:-vi}" tutorial
```

```nginx
server {
       listen 80;
       listen [::]:80;

       server_name *.mydomain.com;

       root /var/www/tutorial;
       index index.html;

       location / {
               try_files $uri $uri/ =404;
       }
}
```

The above config is just a simple nginx server that listens on a wildcard path returning a simple response.

6. In your publicly available server, use `certbot` with the [manual](https://certbot.eff.org/docs/using.html#manual) plugin as the authenticator and the [nginx](https://certbot.eff.org/docs/using.html#nginx) plugin as the installer to grant your wildcard cert:

```bash
# server with publicly available static ip
certbot run -a manual -i nginx -d *.mydomain.com
```

7. When prompted, create a TXT record in your DNS like below:


![sample_txt_record](https://i.imgur.com/n3TEPBg.png)

Be careful to not put your domain in as the Host in the TXT record

8. Wait until your TXT record propogates through the Internet's DNS servers. You can use a site like https://mxtoolbox.com/SuperTool.aspx

9. When you successfully acquire your wildcard cert, create the Kubernetes TLS secret in your publicly available server, like below:

```bash
# server with publicly available static ip

# only sudo has access to the directory we need to get to
sudo -s
cd /etc/letsencrypt/live/mydomain.com/
# create the TLS secret
kubectl create secret tls mydomain-dot-com-wildcard-tls --cert fullchain.pem --key privkey.pem --dry-run -o yaml > mydomain-com-wildcard-tls.yaml
# move the yaml file to someplace you'll be able to scp from on your local machine, likely your user's home directory
mv mydomain-com-wildcard-tls.yaml /home/myuser/
```

10. Move your secret to your local machine

```bash
# local machine

scp my_user@my_server_ip:/home/myuser/mydomain-com-wildcard-tls.yaml .
```

11. You likely want to change the namespace of your secret so that when you apply it it's available for your service to reference by name. Change `metadata.namespace` accordingly, for example:
```yaml
# mydomain-com-wildcard-tls.yaml
...
metadata:
  namespace: my-namespace
...
```

12. Apply the secret

```bash
kubectl apply mydomain-com-wildcard-tls.yaml
```

13. You can now guard your service using your newly created cert. Here's an example of [TLS termination](https://kubernetes.github.io/ingress-nginx/examples/tls-termination/) using [ingress-nginx](ingress-nginx/README.md)

14. Oh yeah, you probably want to delete your NGINX web server instance so as not keeping your TLS secrets "exposed"....