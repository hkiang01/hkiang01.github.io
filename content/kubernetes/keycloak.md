---
title: "Keycloak"
weight: 1
draft: false
---

[Keycloak] is an identity management solution useful for securing applications in Kubernetes.
This post shows how to set up Keycloak and secure an application in Kubernetes with Keycloak.

- [Installing Keycloak](#installing-keycloak)
  - [Simple first](#simple-first)
  - [Database for production readiness](#database-for-production-readiness)
    - [Creating the chart](#creating-the-chart)
    - [Adding Postgres](#adding-postgres)


## Installing Keycloak

### Simple first

We're going to see what it takes to minimally get Keycloak to run in Kubernetes.
First, we'll create a namespace called keycloak

```bash
kubectl create namespace keycloak
```

We'll then get the quickstart manifest from https://github.com/keycloak/keycloak-quickstarts/tree/latest/kubernetes-examples.
I've made a few edits, namely:

- Service type changed to ClusterIP
- namespaces changed to "keycloak"

I'll call mine keycloak.yaml

```yaml
# keycloak.yaml
apiVersion: v1
kind: Service
metadata:
  name: keycloak
  namespace: keycloak
  labels:
    app: keycloak
spec:
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  selector:
    app: keycloak
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keycloak
  namespace: keycloak
  labels:
    app: keycloak
spec:
  replicas: 1
  selector:
    matchLabels:
      app: keycloak
  template:
    metadata:
      labels:
        app: keycloak
    spec:
      containers:
      - name: keycloak
        image: quay.io/keycloak/keycloak:11.0.2
        env:
        - name: KEYCLOAK_USER
          value: "admin"
        - name: KEYCLOAK_PASSWORD
          value: "admin"
        - name: PROXY_ADDRESS_FORWARDING
          value: "true"
        ports:
        - name: http
          containerPort: 8080
        - name: https
          containerPort: 8443
        readinessProbe:
          httpGet:
            path: /auth/realms/master
            port: 8080
```

Let's apply it
```zsh
kubectl apply -f keycloak.yaml
```

Let's make sure it's up and running:

```zsh
kubectl get all -n keycloak
```

You should see that the pods are all ready.
Below, 1 of 1 pods are ready, as indicated by 1/1.

```txt
NAME                            READY   STATUS    RESTARTS   AGE
pod/keycloak-6bc5f6d94c-bdbln   1/1     Running   0          3m25s

NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/keycloak   ClusterIP   10.152.183.91   <none>        8080/TCP   3m26s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/keycloak   1/1     1            1           3m25s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/keycloak-6bc5f6d94c   1         1         1       3m25s
```

To access the app, we'll need to port-forward the service:
```zsh
kubectl -n keycloak port-forward svc/keycloak 8080
```

You should see output like the following:
```txt
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
```

We should now be able to access the instance at http://localhost:8080 in our browser.
Before we continue, let's do some cleanup:

```zsh
kubectl delete -f keycloak.yaml
```

### Database for production readiness

#### Creating the chart

Keycloak is a stateful application that is backed by a database like Postgres.
We're going to take the above manifest from [Installing Keycloak](##installing-keycloak) and paste it as a template in a new Helm chart with Postgres as a package [dependency](https://helm.sh/docs/chart_best_practices/dependencies/#helm).
You can use an existing chart, but I think it's valuable to see what a minimal chart looks like.

Let's first create a chart called keycloak:

```zsh
helm create keycloak
```

This is the file tree of what's created

```
├── keycloak
│   ├── charts
│   ├── Chart.yaml
│   ├── templates
│   │   ├── deployment.yaml
│   │   ├── _helpers.tpl
│   │   ├── hpa.yaml
│   │   ├── ingress.yaml
│   │   ├── NOTES.txt
│   │   ├── serviceaccount.yaml
│   │   ├── service.yaml
│   │   └── tests
│   │       └── test-connection.yaml
│   └── values.yaml
```

We can get rid of the following in templates/:
- hpa.yaml
- tests/

```zsh
cd keycloak/templates/
rm -rf hpa.yaml tests/
```

Let's configure the chart to use the keycloak image.
We can accomplish this with the follwing in values.yaml at the root of the chart.

```yaml
# values.yaml
image:
  repository: quay.io/keycloak/keycloak
  pullPolicy: IfNotPresent
  # Overrides the image tag whose default is the chart appVersion.
  tag: "11.0.2"
```

And configure our credentials:

{{% notice warning %}}
You should never store secrets in plaintext in your repo history.
The snippet below is for demonstration purposes only.
{{% /notice %}}

```yaml
# values.yaml
username: admin
password: supersecretpassword
```

{{% notice tip %}}
You can use [Sealed Secrets for Kubernetes](https://github.com/bitnami-labs/sealed-secrets) and store secrets in encrypted form in your chart's templates.
See [Usage](https://github.com/bitnami-labs/sealed-secrets#usage) to get started.
{{% /notice %}}

The container environment variables, ports, and probes will have to be copied over as well.
```yaml
# templates/deployment.yaml
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          env:
          - name: KEYCLOAK_USER
            value: {{ .Values.username }}
          - name: KEYCLOAK_PASSWORD
            value: {{ .Values.password }}
          - name: PROXY_ADDRESS_FORWARDING
            value: "true"
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
            - name: https
              containerPort: 8443
          livenessProbe:
            httpGet:
              path: /
              port: http
          readinessProbe:
            httpGet:
              path: /auth/realms/master
              port: http
```

We can now test our chart to make sure we have the same level of access as before.
Perform the following command in a directory containing the keycloak/ directory that is the chart we created:

```zsh
helm -n keycloak upgrade --install keycloak ./keycloak
```

Port-forward the service:

```
kubectl -n keycloak port-forward svc/keycloak 8080:80
```

We should now be able to access the instance at http://localhost:8080 in our browser.

#### Adding Postgres

The reason we want to add Postgresql via a Helm dependency is that a lot of the legwork with respect to ensuring availability and persistence is already done for you.
There are packages that offer [high availability](https://artifacthub.io/packages/helm/bitnami/postgresql-ha), but here we'll just go for the standard [postgresql](https://artifacthub.io/packages/helm/bitnami/postgresql) package.

Let's add the dependency:

```yaml
# Chart.yaml
dependencies:
- name: postgresql
  version: 9.8.6
  repository: https://charts.bitnami.com/bitnami
```

Pull the dependency:

```zsh
helm dependency update ./keycloak
```

You should see output like below:

```txt
...Successfully got an update from the "bitnami" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Downloading postgresql from repo https://charts.bitnami.com/bitnami
Deleting outdated charts
```

You can now observe the chart itself.
We're going to configure it by continuing to edit the same values.yaml file we used to set the chart's image to keycloak to configure out secrets

{{% notice warning %}}
You should never store secrets in plaintext in your repo history.
The snippet below is for demonstration purposes only.
{{% /notice %}}


```yaml
# values.yaml
postgresql:
  postgresqlUsername: postgres
  postgresqlPassword: secretpassword
  postgresqlDatabase: keycloak
  service:
    port: 5432
```

{{% notice tip %}}
Use a Kubernetes Secret to define your credentials and point `postgresql.existingSecret` in values.yaml to it.
You can use [Sealed Secrets for Kubernetes](https://github.com/bitnami-labs/sealed-secrets) and store secrets in encrypted form in your chart's templates.
See [Usage](https://github.com/bitnami-labs/sealed-secrets#usage) to get started.
{{% /notice %}}

Now we have to make Keycloak talk to Postgres.

```yaml
# templates/deployment.yaml
          env:
          - name: KEYCLOAK_USER
            value: {{ .Values.username }}
          - name: KEYCLOAK_PASSWORD
            value: {{ .Values.password }}
          - name: PROXY_ADDRESS_FORWARDING
            value: "true"
          - name: DB_VENDOR
            value: postgres
          - name: DB_ADDR
            value: {{ include "keycloak.fullname" . }}-postgresql
          - name: DB_PORT
            value: {{ .Values.postgresql.service.port | quote }}
          - name: DB_DATABASE
            value: {{ .Values.postgresql.postgresqlDatabase }}
          - name: DB_USER
            value: {{ .Values.postgresql.postgresqlUsername }}
          - name: DB_PASSWORD
            value: {{ .Values.postgresql.postgresqlPassword }}
```

Deploy the chart:

```zsh
helm -n keycloak upgrade --install keycloak ./keycloak
```

You should see output like the following:

```txt
Release "keycloak" has been upgraded. Happy Helming!
NAME: keycloak
LAST DEPLOYED: Sun Oct 25 01:02:10 2020
NAMESPACE: keycloak
STATUS: deployed
REVISION: 5
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace keycloak -l "app.kubernetes.io/name=keycloak,app.kubernetes.io/instance=keycloak" -o jsonpath="{.items[0].metadata.name}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace keycloak port-forward $POD_NAME 8080:80
```


By following the instructions from the output above, you should be able to access an instance of keycloak backed by Postgres.

To validate that your instance is backed by Postgres, you can tail the logs of the Keycloak pod:

```zsh
kubectl -n keycloak logs -f -l=app.kubernetes.io/name=keycloak
```

You should see output like below:

```txt
=========================================================================

  Using PostgreSQL database

=========================================================================
...
```


[Keycloak]: https://www.keycloak.org/