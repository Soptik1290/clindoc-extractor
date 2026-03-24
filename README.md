# ClinDoc Extractor

**ClinDoc Extractor** je backendová služba pro strukturovanou extrakci klinických entit z lékařských diktátů a textů (propouštěcí zprávy, ambulantní záznamy). Služba používá hybridní přístup kombinující LLM s garantovaným formátováním (Structured Outputs) a deterministický Regex fallback.

---

## 1. Quickstart

### Přes Docker (Doporučeno)
```bash
# Sestavení a spuštění pomocí Docker Compose (vyžaduje .env soubor)
docker compose up --build
```

### Lokálně
```bash
# Instalace s vývojovými závislostmi
pip install -e ".[dev]"

# Spuštění serveru
uvicorn app.main:app --reload

# Spuštění testů
pytest tests/ -v --cov=app
```

---

## 2. Architektura a volba přístupu

Rozhodli jsme se pro **LLM (gpt-5.4-nano) jako primární motor** doplněný o **Regex fallback**.

- **Proč ne čístý regex:** Zdravotnické texty jsou velmi nestrukturované a obsahují spoustu překlepů, různých formátů a zkratek, které nelze rozumným množstvím regulárních výrazů pokrýt. Cílem je mít vysoký *recall*, což regex omezuje.
- **Proč ne předtrénované NLP knihovny:** Spacy/medspaCy fungují skvěle na angličtině, ale pro češtinu v medicínské doméně chybí kvalitní modely, což ztěžuje univerzálnost na CEE trhu. LLM si s kontextem čeština vs. latina poradí mnohem lépe.
- **Proč model gpt-5.4-nano:** Tento model nabízí ideální poměr ceny ($0.20 / 1M tokenů) a výkonu s ohledem na rychlost odpovědi, přičemž je dedikovaný přímo na úlohy strukturované datové extrakce. K efektivitě velmi přispívají "Structured Outputs", které garantují výstup dle našeho Pydantic schématu.
- **Pipeline fungování:**
    1. Požadavek jde do `ExtractionPipeline`.
    2. Model vytěží primárně přes API `gpt-5.4-nano`.
    3. Pokud proces selže například na OpenAI API výpadku nebo time-outu (nastavený timeout: 10 sekund), pipeline nezhavaruje, ale na text aplikuje `RegexExtractor`, jenž používá bezpečné regulární výrazy na vyzvednutí nejdůležitějších polí.

---

## 3. API dokumentace

Služba vystavuje Swagger UI na adrese `http://localhost:8000/docs`.

### POST `/extract`
Extrahuje data z textu.

**Request:**
```json
{
  "text": "Pacient Jan Novak, datum narozeni 15.3.1968, byl prijat 12.11.2024 pro akutni ischemickou CMP...",
  "language": "auto"
}
```

**Response (200 OK):**
```json
{
  "patient": {
    "name": "Jan Novak",
    "birth_date": "1968-03-15"
  },
  "vitals": {
    "bp": "178/95",
    "spo2": "97%",
    "hr": null,
    "temperature": null
  },
  "diagnoses": [
    {
      "code": "I63.9",
      "system": "ICD-10",
      "text": null
    }
  ],
  "medications": [
    {
      "name": "aspirin",
      "dose": "100mg",
      "frequency": "1x denne",
      "route": null
    }
  ],
  "dates": {
    "admission": "2024-11-12",
    "discharge": null
  },
  "follow_up": "kontrola u neurologa za 6 tydnu",
  "confidence": 0.85,
  "field_confidence": {
    "patient.name": {"value": 0.95, "reason": "Clearly readable name"}
  },
  "warnings": [],
  "extraction_method": "llm"
}
```

### Další Endpointy (Bonusy)
- `POST /extract/fhir`: Odpoví plně formátovaným **HL7 FHIR R4 Bundlem** contenanting (Patient, Condition, MedicationRequest).
- `POST /submit`: Asynchronní odeslání textu k extrakci do Redis fronty. (Vrací `job_id`).
- `GET /result/{job_id}`: Zjištění výsledku asynchronní operace.
- Skryté testovací UI přímo na `http://localhost:8000/`.

**Příklad přes cURL:**
```bash
curl -X 'POST' \
  'http://localhost:8000/extract' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Pt. Maria Horakova, DOB 22/07/1975, presented with chest pain...",
  "language": "auto"
}'
```

### GET `/health`
Zkontroluje, zda služba běží.
```bash
curl http://localhost:8000/health
```

---

## 4. Známá omezení

- **Nedeterministické chování LLM:** U jakéhokoliv LLM modelu je potřeba počítat s tím, že na úplně totožný nejednoznačný vstup může vygenerovat mírně jiný extrahovaný tvar textových instrukcí.
- **Omezený recall Regex fallbacku:** Pokud selže LLM a sepne fallback, regulární výrazy chytnou pouze úzce vymezené patterny. Na jakémkoliv odchýleném zápisu (`tlak sto-osmdesat na devadesat`) selžou.
- **Kalibrace skórovaní (Confidence):** Systém momentálně generuje *confidence score* přes deterministický field-level Prompt Engineering, to skóre nemusí ale být 100% kalibrované pro všechny out-of-distribution texty oproti soft-max pravděpodobnosti u finetunovaných modelů.

---

## 5. Co bych zlepšil v produkci

- **Bezpečnost a GDPR data:** Odesílání surových pacientských zpráv (s celými jmény, adresami a daty narození) komerčním LLM spadá do šedé zóny. Pipeline by měla nejdříve surová PII lokalizovat lokálním modelem, anonymizovat je a odesílat modifikovaný text. De-anonymizace by následovala při formování responze.
- **Lokální specializovaný LLM:** Finetuned malý český medicínský LLM (Llama, Mistral) provozovaný v on-premise prostředí. Předešlo by se závislosti na internetovém spojení a nákladům z per-token pricingů u OpenAI.
- **Validace vůči FHIR standardu:** Transformace outputů do plného FHIR mapování je sice implementována (jako bonus), ale v produkci by se měla navíc validovat vůči oficiálnímu lokálnímu logickému *FHIR Validatoru* běžícímu např. v sidecar kontejneru.
- **Garance doručení a Persistence (MQ):** Asynchronní odpovědi LLM a Redis fronta jsou implementovány, ale měly by používat perzistentní broker typu RabbitMQ/Celery, který zaručí, že nepředvídatelně dlouhý Job získá re-try kapacitu po restartu workeru.
- **Monitoring a latence:** Trackování LLM requests a fallback rates pomocí nástrojů jako Prometheus / LangSmith pro optimalizaci promptů.
- **API Autentizace a RBAC:** Zabezpečení hlaviček (OAuth2 / JWT tokens).

---

## 6. Použité AI nástroje

Tento projekt byl vyvíjen s pomocí asistenčního AI kódujícího enginu pro návrh architektury, generování boilerplate kódu, testovacích případů a ladění strukturovaných regex promptů. Veškerý kód byl zkontrolován, zkompletován a upraven autorem řešení.
