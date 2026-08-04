# AccessHub

Mała aplikacja REST API napisana w czystym Pythonie (biblioteka standardowa,
bez frameworków), symulująca uproszczony proces zarządzania dostępem:
użytkownicy proszą o rolę, admin akceptuje/odrzuca wniosek. To celowo
przypomina workflow znany z IAM/IdentityIQ (request → approval → grant),
żeby logika biznesowa była Ci znajoma, a cała energia poszła w naukę
DevOps/DevSecOps.

Ten projekt **celowo nie zawiera** żadnych plików Dockera, Kubernetesa,
Terraform ani GitLab CI/CD — to Twoje zadanie do zbudowania samodzielnie,
jako ćwiczenie. Poniżej masz plan.

## Architektura

```
app/
  main.py       - punkt wejścia, uruchamia serwer HTTP
  handlers.py   - routing + logika żądań (http.server, bez frameworku)
  db.py         - warstwa persystencji (SQLite, bez ORM)
  models.py     - modele domenowe (User, Role, AccessRequest)
  config.py     - konfiguracja z zmiennych środowiskowych
  logger.py     - logowanie do stdout
tests/
  test_db.py    - testy jednostkowe warstwy danych
  test_api.py   - testy integracyjne API (HTTP)
```

## Uruchomienie lokalnie

```bash
pip install -r requirements.txt
python -m app.main
```

Serwer wystartuje domyślnie na `0.0.0.0:8080`.

## Konfiguracja (zmienne środowiskowe)

| Zmienna                 | Domyślna wartość      | Opis                                   |
|--------------------------|------------------------|-----------------------------------------|
| `ACCESSHUB_HOST`          | `0.0.0.0`              | Adres nasłuchu                          |
| `ACCESSHUB_PORT`          | `8080`                 | Port nasłuchu                           |
| `ACCESSHUB_DB_PATH`       | `data/accesshub.db`    | Ścieżka do pliku SQLite                 |
| `ACCESSHUB_LOG_LEVEL`     | `INFO`                 | Poziom logowania                        |
| `ACCESSHUB_ADMIN_TOKEN`   | `change-me`            | Token wymagany do operacji admina       |

To celowo jest zewnętrznie konfigurowalne — to jest właśnie "seam", w który
później podepniesz Docker ENV / K8s ConfigMap i Secret / Terraform outputs.

## API

- `GET  /health` — health check (przyda się do liveness/readiness probes w K8s)
- `POST /users` `{"username": "..."}`
- `GET  /users`
- `POST /roles` `{"name": "...", "description": "..."}` — wymaga nagłówka `X-Admin-Token`
- `GET  /roles`
- `POST /access-requests` `{"user_id": 1, "role_id": 1}`
- `GET  /access-requests`
- `POST /access-requests/{id}/approve` — wymaga `X-Admin-Token`
- `POST /access-requests/{id}/reject` — wymaga `X-Admin-Token`

## Testy

```bash
python -m pytest tests/ -v
```

## Celowe "niedoskonałości" do naprawienia jako ćwiczenia DevSecOps

Te rzeczy zostały zostawione specjalnie, żebyś miał co poprawiać:

- `ACCESSHUB_ADMIN_TOKEN` ma słaby domyślny sekret w kodzie — dobre
  ćwiczenie do sekret-managementu (K8s Secret, GitLab CI/CD masked
  variables, docelowo np. Vault).
- Baza SQLite to pojedynczy plik — dobre ćwiczenie do PersistentVolume
  w K8s i do przemyślenia, co się stanie przy restarcie poda bez wolumenu.
- Brak żadnego rate-limitingu / walidacji nagłówków — dobry temat na
  security scanning w CI/CD (np. SAST/dependency scanning w GitLab).
- Aplikacja loguje do stdout w prostym formacie tekstowym — dobre
  ćwiczenie do przejścia na JSON logging pod kątem agregacji logów.

## Sugerowana ścieżka nauki (na tym repo)

1. **Docker** — napisz `Dockerfile` (najlepiej multi-stage), zbuduj obraz,
   uruchom kontener, zmapuj port i wolumen na `data/`. Potem dodaj
   `docker-compose.yml`, jeśli zechcesz osobny kontener na coś (np. przyszły
   Postgres zamiast SQLite).
2. **Kubernetes** — napisz manifesty: `Deployment`, `Service`, `ConfigMap`
   (dla `ACCESSHUB_LOG_LEVEL` itp.), `Secret` (dla `ACCESSHUB_ADMIN_TOKEN`),
   `PersistentVolumeClaim` (dla bazy), liveness/readiness probe na `/health`.
   Później: `Ingress`, `HorizontalPodAutoscaler`, `NetworkPolicy` (dobre
   pod kątem DevSecOps).
3. **Terraform** — jeśli wdrażasz do chmury (np. do klastra K8s w AWS/GCP/Azure
   albo lokalnie do minikube/kind), opisz infrastrukturę jako kod: klaster,
   sieć, może rejestr obrazów. Zacznij od czegoś prostego, np. providera
   `kubernetes` do zarządzania samymi manifestami przez Terraform.
4. **GitLab CI/CD** — pipeline: lint (`ruff`/`flake8`) → testy (`pytest`) →
   build obrazu Dockera → skan bezpieczeństwa obrazu (np. Trivy) → push do
   registry → deploy do K8s (przez `kubectl`/Helm/Terraform). To naturalne
   miejsce, żeby dodać SAST/dependency scanning i poczuć się jak
   DevSecOps, a nie tylko DevOps.

Powodzenia z przebranżowieniem — masz mocny fundament w IAM, a ten projekt
został tak dobrany (workflow request/approval), żeby logika była Ci bliska
i żebyś mógł się skupić w 100% na warstwie infrastruktury.
