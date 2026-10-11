import 'dart:convert';
import 'package:http/http.dart' as http;

/// CypherPunks In-Vehicle Diagnostics Chat Service for Flutter
///
/// Features:
/// 1. API Key Authentication: Prevents unauthorized abuse.
/// 2. Strict Topic Restriction: Automatically blocks non-vehicle questions.
/// 3. Adaptive Responses: Delivers brief, crisp solutions for small doubts
///    and full safety triage for emergency breakdowns.
class VehicleChatService {
  // Replace this with your deployed Render URL:
  // e.g. 'https://cypherpunks-vehicle-ai.onrender.com'
  final String baseUrl;
  
  // The secret API Key configured in your backend
  final String apiKey;
  
  // Preserves multi-turn conversation memory
  String? sessionId;

  VehicleChatService({
    required this.baseUrl,
    this.apiKey = 'cypherpunks-secret-key-2024',
  });

  /// Sends a vehicle problem or doubt to the AI backend
  Future<Map<String, dynamic>> sendMessage(String userMessage) async {
    final url = Uri.parse('$baseUrl/api/chat');

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-API-Key': apiKey, // API Key authentication
        },
        body: jsonEncode({
          'message': userMessage,
          if (sessionId != null) 'session_id': sessionId,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        
        // Save session id for subsequent messages
        sessionId = data['session_id'];

        return {
          'success': true,
          // True if query was about vehicle problems; False if off-topic and stopped
          'isCarRelated': data['is_car_related'] as bool,
          'response': data['response'] as String,
          'urgency': data['urgency'] as String,
        };
      } else if (response.statusCode == 401) {
        return {
          'success': false,
          'error': 'Unauthorized: API Key mismatch or missing. Check your X-API-Key.',
        };
      } else {
        return {
          'success': false,
          'error': 'Server error (${response.statusCode}): ${response.body}',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'error': 'Network connection error: $e',
      };
    }
  }

  /// Emergency SOS trigger for stranded driver
  Future<Map<String, dynamic>> triggerSOS({
    required String locationDesc,
    required String issueType,
    String? phone,
  }) async {
    final url = Uri.parse('$baseUrl/api/sos');

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: jsonEncode({
          'location_desc': locationDesc,
          'issue_type': issueType,
          'phone': phone ?? 'Unknown',
        }),
      );

      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (e) {
      return {'status': 'ERROR', 'message': e.toString()};
    }
  }
}
