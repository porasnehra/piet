# How to Deploy to Render & Connect Flutter Frontend

## 1. Quick Deploy to Render (Free)

1. Push this folder to your **GitHub** repository.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. Render settings:
   - **Name**: `cypherpunks-vehicle-ai` (or your preferred name)
   - **Language / Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Under **Environment Variables**, add:
   - `GOOGLE_API_KEY`: *(Your Google Gemini API Key from `.env`)*
   - `APP_API_KEY`: `cypherpunks-secret-key-2024` *(Or custom secret key to protect your backend)*
7. Click **Create Web Service**.
8. Once deployed, Render will give you a live URL, for example:
   `https://cypherpunks-vehicle-ai.onrender.com`

---

## 2. API Endpoint Specification for Flutter

### Base URL:
`https://<your-render-app-name>.onrender.com`

### 1. Chat & Diagnostics Endpoint
- **URL**: `POST /api/chat`
- **Headers**:
  ```http
  Content-Type: application/json
  X-API-Key: cypherpunks-secret-key-2024
  ```
- **Request Body (JSON)**:
  ```json
  {
    "message": "My engine is overheating and needle is in red",
    "session_id": "optional-unique-session-id"
  }
  ```
- **Response Body (200 OK)**:
  ```json
  {
    "session_id": "4a7f2e1a-...",
    "is_car_related": true,
    "response": "🚨 Immediate Safety Action: ...",
    "urgency": "IN_SCOPE_DIAGNOSED"
  }
  ```

### 2. If User Asks an Off-Topic / Wrong Question:
- `is_car_related` will be `false`
- `response` will explain that it only answers car problems and will stop answering non-vehicle queries:
  ```json
  {
    "session_id": "...",
    "is_car_related": false,
    "response": "⛔ Out of Scope Request\n\nI am the CypherPunks AI Roadside Assistance & Vehicle Emergency Assistant...",
    "urgency": "OUT_OF_SCOPE"
  }
  ```

### 3. If User Asks a Small Doubt:
- The AI automatically detects small doubts and returns a **brief, concise 2-3 bullet solution** instead of a lengthy essay.

---

## 3. Flutter Dart Code for Your Friend

Copy and paste [`flutter_service_example.dart`](file:///e:/Piet/flutter_service_example.dart) into your Flutter project:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class VehicleChatService {
  // Your deployed Render URL
  final String baseUrl = 'https://YOUR_APP_NAME.onrender.com';
  final String apiKey = 'cypherpunks-secret-key-2024';
  String? sessionId;

  Future<Map<String, dynamic>> askAssistant(String userMessage) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/chat'),
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: jsonEncode({
        'message': userMessage,
        if (sessionId != null) 'session_id': sessionId,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      sessionId = data['session_id'];
      return {
        'isCar': data['is_car_related'], // false if off-topic
        'text': data['response'],
      };
    } else if (response.statusCode == 401) {
      return {'isCar': false, 'text': 'API Key Unauthorized'};
    } else {
      return {'isCar': false, 'text': 'Error: ${response.statusCode}'};
    }
  }
}
```
