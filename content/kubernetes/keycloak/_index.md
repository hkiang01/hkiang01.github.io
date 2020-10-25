---
title: "Keycloak"
date: 2020-10-25T21:30:00-05:00
draft: true
---

# Keycloak

[Keycloak] is an identity management solution useful for securing applications in Kubernetes.
This post shows how to set up Keycloak and secure an application in Kubernetes with Keycloak.

## Installing Keycloak

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

```bash
kubectl get all -n keycloak
NAME                            READY   STATUS    RESTARTS   AGE
pod/keycloak-6bc5f6d94c-bdbln   1/1     Running   0          3m25s

NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/keycloak   ClusterIP   10.152.183.91   <none>        8080/TCP   3m26s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/keycloak   1/1     1            1           3m25s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/keycloak-6bc5f6d94c   1         1         1       3m25s
```

To access the app, we'll need to port-forward the service

```zsh
kubectl -n keycloak port-forward svc/keycloak 8080

Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
```

We should now be able to access the instance at http://localhost:8080 in our browser.
Before we continue, let's do some cleanup:

```zsh
kubectl delete -f keycloak.yaml
```

## Database for production readiness

### Creating the chart

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
image:
  repository: quay.io/keycloak/keycloak
  pullPolicy: IfNotPresent
  # Overrides the image tag whose default is the chart appVersion.
  tag: "11.0.2"
```

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
            value: "admin"
          - name: KEYCLOAK_PASSWORD
            value: "admin"
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

Port-foward the service

```
kubectl -n keycloak port-forward svc/keycloak 8080:80
```

We should now be able to access the instance at http://localhost:8080 in our browser.

### Adding Postgres

[Keycloak]: https://www.keycloak.org/