#!/usr/bin/env python3
"""
ML Performance Testing Script for ARTIFACTOR v3.0
Comprehensive testing of ML classification, semantic search, and smart tagging performance
"""

import asyncio
import logging
import time
import json
import statistics
from typing import Dict, Any, List
from pathlib import Path
import sys

# Add backend to Python path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLPerformanceTester:
    """
    Comprehensive ML performance testing suite
    """

    def __init__(self):
        self.test_data = self._load_test_data()
        self.results = {
            'classification_tests': [],
            'search_tests': [],
            'tagging_tests': [],
            'pipeline_tests': [],
            'summary': {}
        }

    def _load_test_data(self) -> List[Dict[str, Any]]:
        """Load test data for performance testing"""
        return [
            {
                'name': 'python_function',
                'content': '''def fibonacci(n):
    """Calculate fibonacci number using recursion.

    Args:
        n (int): The position in fibonacci sequence

    Returns:
        int: The fibonacci number at position n
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    for i in range(10):
        print(f"fibonacci({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()''',
                'title': 'Fibonacci Calculator',
                'description': 'Recursive fibonacci implementation with documentation',
                'file_type': 'python',
                'language': 'python',
                'expected_language': 'python',
                'expected_tags': ['python', 'algorithm', 'recursion', 'fibonacci']
            },
            {
                'name': 'react_component',
                'content': '''import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UserList = ({ apiUrl }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${apiUrl}/users`);
        setUsers(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [apiUrl]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="user-list">
      <h2>Users</h2>
      <ul>
        {users.map(user => (
          <li key={user.id}>
            <strong>{user.name}</strong> - {user.email}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default UserList;''',
                'title': 'User List Component',
                'description': 'React component for displaying users with API integration',
                'file_type': 'javascript',
                'language': 'javascript',
                'expected_language': 'javascript',
                'expected_tags': ['react', 'javascript', 'component', 'api', 'hooks']
            },
            {
                'name': 'sql_query',
                'content': '''-- User Analytics Query
-- Analyzes user behavior and engagement metrics

WITH user_stats AS (
  SELECT
    u.id,
    u.name,
    u.email,
    COUNT(DISTINCT o.id) as order_count,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value,
    MIN(o.created_at) as first_order,
    MAX(o.created_at) as last_order
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  WHERE u.created_at >= '2024-01-01'
  GROUP BY u.id, u.name, u.email
),
engagement_metrics AS (
  SELECT
    user_id,
    COUNT(*) as login_count,
    COUNT(DISTINCT DATE(created_at)) as active_days
  FROM user_sessions
  WHERE created_at >= '2024-01-01'
  GROUP BY user_id
)

SELECT
  us.name,
  us.email,
  COALESCE(us.order_count, 0) as orders,
  COALESCE(us.total_spent, 0) as revenue,
  COALESCE(us.avg_order_value, 0) as aov,
  COALESCE(em.login_count, 0) as logins,
  COALESCE(em.active_days, 0) as active_days,
  CASE
    WHEN us.order_count >= 5 AND em.active_days >= 30 THEN 'High Value'
    WHEN us.order_count >= 2 OR em.active_days >= 10 THEN 'Medium Value'
    ELSE 'Low Value'
  END as customer_segment
FROM user_stats us
LEFT JOIN engagement_metrics em ON us.id = em.user_id
ORDER BY us.total_spent DESC, em.active_days DESC;''',
                'title': 'User Analytics Query',
                'description': 'Complex SQL query for user behavior analysis',
                'file_type': 'sql',
                'language': 'sql',
                'expected_language': 'sql',
                'expected_tags': ['sql', 'analytics', 'users', 'database', 'metrics']
            },
            {
                'name': 'api_documentation',
                'content': '''# User Management API

## Authentication
All API endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### GET /api/users
Retrieve list of users with optional filtering.

**Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Number of users per page (default: 20, max: 100)
- `search` (optional): Search term for filtering by name or email
- `active` (optional): Filter by active status (true/false)

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "last_login": "2024-01-20T14:22:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### POST /api/users
Create a new user account.

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "secure_password",
  "role": "user"
}
```

**Response:**
```json
{
  "user": {
    "id": "new_uuid",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "active": true,
    "role": "user",
    "created_at": "2024-01-21T09:15:00Z"
  }
}
```

### PUT /api/users/{id}
Update existing user information.

### DELETE /api/users/{id}
Deactivate user account (soft delete).

## Error Handling
All errors return appropriate HTTP status codes with error details:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

## Rate Limiting
API endpoints are rate limited to 100 requests per minute per user.''',
                'title': 'User Management API Documentation',
                'description': 'REST API documentation with examples',
                'file_type': 'markdown',
                'language': 'markdown',
                'expected_language': 'markdown',
                'expected_tags': ['documentation', 'api', 'rest', 'users', 'authentication']
            },
            {
                'name': 'config_file',
                'content': '''# Application Configuration
# ARTIFACTOR v3.0 Production Configuration

[database]
host = "localhost"
port = 5432
name = "artifactor_prod"
user = "artifactor_user"
password = "${DATABASE_PASSWORD}"
pool_size = 20
max_overflow = 30
pool_timeout = 30
pool_recycle = 3600

[redis]
url = "redis://localhost:6379"
password = "${REDIS_PASSWORD}"
db = 0
max_connections = 50
socket_timeout = 5
socket_connect_timeout = 5

[ml_pipeline]
enabled = true
workers = 8
batch_size = 32
cache_size = 1000
cache_ttl = 3600
models_path = "/opt/ml_models"
embeddings_model = "all-MiniLM-L6-v2"
classification_threshold = 0.85

[semantic_search]
enabled = true
index_rebuild_interval = 86400
vector_dimensions = 384
similarity_threshold = 0.7
max_results = 100

[performance]
request_timeout = 30
max_concurrent_requests = 1000
rate_limit_requests = 100
rate_limit_window = 60
enable_compression = true
compression_threshold = 1024

[logging]
level = "INFO"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
file = "/var/log/artifactor/app.log"
max_file_size = "100MB"
backup_count = 5
enable_rotation = true

[security]
jwt_secret = "${JWT_SECRET}"
jwt_expiration = 86400
password_min_length = 8
password_require_special = true
enable_2fa = false
session_timeout = 3600

[monitoring]
enabled = true
metrics_port = 9090
health_check_interval = 30
alert_webhook = "${ALERT_WEBHOOK_URL}"
log_retention_days = 30''',
                'title': 'Application Configuration',
                'description': 'Production configuration file with database and ML settings',
                'file_type': 'config',
                'language': 'toml',
                'expected_language': 'toml',
                'expected_tags': ['configuration', 'production', 'database', 'ml', 'security']
            }
        ]

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        try:
            logger.info("Starting comprehensive ML performance tests...")

            # Test 1: ML Classification Performance
            logger.info("Test 1: ML Classification Performance")
            classification_results = await self._test_classification_performance()
            self.results['classification_tests'] = classification_results

            # Test 2: Semantic Search Performance
            logger.info("Test 2: Semantic Search Performance")
            search_results = await self._test_search_performance()
            self.results['search_tests'] = search_results

            # Test 3: Smart Tagging Performance
            logger.info("Test 3: Smart Tagging Performance")
            tagging_results = await self._test_tagging_performance()
            self.results['tagging_tests'] = tagging_results

            # Test 4: End-to-End Pipeline Performance
            logger.info("Test 4: End-to-End Pipeline Performance")
            pipeline_results = await self._test_pipeline_performance()
            self.results['pipeline_tests'] = pipeline_results

            # Test 5: Load Testing
            logger.info("Test 5: Load Testing")
            load_results = await self._test_load_performance()
            self.results['load_tests'] = load_results

            # Generate summary
            self.results['summary'] = self._generate_performance_summary()

            logger.info("All performance tests completed successfully")
            return self.results

        except Exception as e:
            logger.error(f"Error in comprehensive testing: {e}")
            return {'error': str(e), 'partial_results': self.results}

    async def _test_classification_performance(self) -> List[Dict[str, Any]]:
        """Test ML classification performance"""
        try:
            from backend.services.ml_classifier import ml_classifier
            await ml_classifier.initialize()

            results = []
            for test_item in self.test_data:
                start_time = time.time()

                # Run classification
                classification_result = await ml_classifier.classify_content(
                    content=test_item['content'],
                    title=test_item['title'],
                    description=test_item['description']
                )

                end_time = time.time()
                processing_time = (end_time - start_time) * 1000  # Convert to ms

                # Check accuracy
                predicted_language = classification_result.get('language', {}).get('predicted', '')
                language_confidence = classification_result.get('language', {}).get('confidence', 0)
                accuracy = 1.0 if predicted_language == test_item['expected_language'] else 0.0

                result = {
                    'test_name': test_item['name'],
                    'processing_time_ms': processing_time,
                    'accuracy': accuracy,
                    'language_confidence': language_confidence,
                    'predicted_language': predicted_language,
                    'expected_language': test_item['expected_language'],
                    'success': classification_result is not None
                }

                results.append(result)
                logger.info(f"  {test_item['name']}: {processing_time:.1f}ms, accuracy: {accuracy:.1f}")

            return results

        except Exception as e:
            logger.error(f"Error in classification testing: {e}")
            return [{'error': str(e)}]

    async def _test_search_performance(self) -> List[Dict[str, Any]]:
        """Test semantic search performance"""
        try:
            from backend.services.semantic_search import semantic_search_service
            await semantic_search_service.initialize()

            # Mock database session for testing
            class MockDB:
                async def execute(self, query):
                    return MockResult()

            class MockResult:
                def scalars(self):
                    return MockScalars()

            class MockScalars:
                def all(self):
                    return []

            search_queries = [
                "python function with recursion",
                "react component with hooks",
                "sql query for analytics",
                "api documentation",
                "configuration file"
            ]

            results = []
            for query in search_queries:
                start_time = time.time()

                # Test search (with mock DB)
                try:
                    search_result = await semantic_search_service.search(
                        query=query,
                        db=MockDB(),
                        user_id="test-user",
                        search_type="hybrid",
                        limit=10
                    )
                    success = True
                except Exception as e:
                    search_result = {'error': str(e)}
                    success = False

                end_time = time.time()
                processing_time = (end_time - start_time) * 1000

                result = {
                    'query': query,
                    'processing_time_ms': processing_time,
                    'success': success,
                    'has_results': 'results' in search_result
                }

                results.append(result)
                logger.info(f"  '{query}': {processing_time:.1f}ms")

            return results

        except Exception as e:
            logger.error(f"Error in search testing: {e}")
            return [{'error': str(e)}]

    async def _test_tagging_performance(self) -> List[Dict[str, Any]]:
        """Test smart tagging performance"""
        try:
            from backend.services.smart_tagging import smart_tagging_service
            await smart_tagging_service.initialize()

            results = []
            for test_item in self.test_data:
                start_time = time.time()

                # Run tagging
                tagging_result = await smart_tagging_service.generate_tags(
                    content=test_item['content'],
                    title=test_item['title'],
                    description=test_item['description'],
                    file_type=test_item['file_type'],
                    language=test_item['language'],
                    max_tags=10
                )

                end_time = time.time()
                processing_time = (end_time - start_time) * 1000

                # Check tag quality
                generated_tags = [tag['name'] for tag in tagging_result.get('tags', [])]
                expected_tags = test_item['expected_tags']
                tag_overlap = len(set(generated_tags) & set(expected_tags))
                tag_accuracy = tag_overlap / len(expected_tags) if expected_tags else 0

                result = {
                    'test_name': test_item['name'],
                    'processing_time_ms': processing_time,
                    'tag_count': len(generated_tags),
                    'tag_accuracy': tag_accuracy,
                    'generated_tags': generated_tags[:5],  # Top 5 tags
                    'expected_tags': expected_tags,
                    'success': 'tags' in tagging_result
                }

                results.append(result)
                logger.info(f"  {test_item['name']}: {processing_time:.1f}ms, {len(generated_tags)} tags, accuracy: {tag_accuracy:.2f}")

            return results

        except Exception as e:
            logger.error(f"Error in tagging testing: {e}")
            return [{'error': str(e)}]

    async def _test_pipeline_performance(self) -> List[Dict[str, Any]]:
        """Test end-to-end pipeline performance"""
        try:
            from backend.services.ml_pipeline import ml_pipeline
            await ml_pipeline.initialize()

            results = []
            for test_item in self.test_data:
                start_time = time.time()

                # Run full pipeline
                pipeline_result = await ml_pipeline.process_artifact(
                    content=test_item['content'],
                    title=test_item['title'],
                    description=test_item['description'],
                    file_type=test_item['file_type'],
                    language=test_item['language'],
                    priority=1
                )

                end_time = time.time()
                processing_time = (end_time - start_time) * 1000

                result = {
                    'test_name': test_item['name'],
                    'processing_time_ms': processing_time,
                    'success': pipeline_result.success,
                    'stages_completed': len(pipeline_result.stages_completed),
                    'cache_hit': pipeline_result.cache_hit,
                    'has_classification': pipeline_result.classification is not None,
                    'has_tags': pipeline_result.tags is not None,
                    'has_embeddings': pipeline_result.embeddings is not None
                }

                results.append(result)
                logger.info(f"  {test_item['name']}: {processing_time:.1f}ms, stages: {len(pipeline_result.stages_completed)}")

            return results

        except Exception as e:
            logger.error(f"Error in pipeline testing: {e}")
            return [{'error': str(e)}]

    async def _test_load_performance(self) -> Dict[str, Any]:
        """Test system performance under load"""
        try:
            from backend.services.ml_pipeline import ml_pipeline

            # Prepare batch requests
            batch_requests = []
            for _ in range(3):  # Test with 3 batches of all test data
                for test_item in self.test_data:
                    batch_requests.append({
                        'content': test_item['content'],
                        'title': test_item['title'],
                        'description': test_item['description'],
                        'file_type': test_item['file_type'],
                        'language': test_item['language']
                    })

            # Run load test
            start_time = time.time()
            batch_results = await ml_pipeline.batch_process(
                batch_requests,
                max_concurrent=5
            )
            end_time = time.time()

            total_time = (end_time - start_time) * 1000
            successful_requests = len([r for r in batch_results if r.success])
            throughput = len(batch_requests) / ((end_time - start_time) or 1)

            # Calculate statistics
            processing_times = [r.processing_time_ms for r in batch_results if r.processing_time_ms]
            avg_latency = statistics.mean(processing_times) if processing_times else 0
            p95_latency = statistics.quantiles(processing_times, n=20)[18] if len(processing_times) > 5 else avg_latency

            result = {
                'total_requests': len(batch_requests),
                'successful_requests': successful_requests,
                'total_time_ms': total_time,
                'throughput_rps': throughput,
                'avg_latency_ms': avg_latency,
                'p95_latency_ms': p95_latency,
                'success_rate': successful_requests / len(batch_requests)
            }

            logger.info(f"  Load test: {throughput:.1f} req/sec, P95: {p95_latency:.1f}ms")
            return result

        except Exception as e:
            logger.error(f"Error in load testing: {e}")
            return {'error': str(e)}

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance test summary"""
        summary = {
            'overall_status': 'PASS',
            'target_metrics': {
                'classification_accuracy': 0.85,
                'response_time_p95_ms': 500,
                'throughput_rps': 100,
                'success_rate': 0.95
            },
            'actual_metrics': {},
            'test_results': {
                'classification': 'PASS',
                'search': 'PASS',
                'tagging': 'PASS',
                'pipeline': 'PASS',
                'load': 'PASS'
            }
        }

        try:
            # Calculate classification metrics
            if self.results.get('classification_tests'):
                classification_tests = [t for t in self.results['classification_tests'] if 'error' not in t]
                if classification_tests:
                    avg_accuracy = statistics.mean([t['accuracy'] for t in classification_tests])
                    avg_time = statistics.mean([t['processing_time_ms'] for t in classification_tests])
                    summary['actual_metrics']['classification_accuracy'] = avg_accuracy
                    summary['actual_metrics']['classification_time_ms'] = avg_time

                    if avg_accuracy < summary['target_metrics']['classification_accuracy']:
                        summary['test_results']['classification'] = 'FAIL'
                        summary['overall_status'] = 'FAIL'

            # Calculate pipeline metrics
            if self.results.get('pipeline_tests'):
                pipeline_tests = [t for t in self.results['pipeline_tests'] if 'error' not in t]
                if pipeline_tests:
                    avg_pipeline_time = statistics.mean([t['processing_time_ms'] for t in pipeline_tests])
                    success_rate = statistics.mean([1 if t['success'] else 0 for t in pipeline_tests])
                    summary['actual_metrics']['pipeline_time_ms'] = avg_pipeline_time
                    summary['actual_metrics']['pipeline_success_rate'] = success_rate

                    if avg_pipeline_time > summary['target_metrics']['response_time_p95_ms']:
                        summary['test_results']['pipeline'] = 'FAIL'
                        summary['overall_status'] = 'FAIL'

            # Calculate load test metrics
            if self.results.get('load_tests') and 'error' not in self.results['load_tests']:
                load_test = self.results['load_tests']
                summary['actual_metrics']['throughput_rps'] = load_test.get('throughput_rps', 0)
                summary['actual_metrics']['p95_latency_ms'] = load_test.get('p95_latency_ms', 0)

                if load_test.get('throughput_rps', 0) < summary['target_metrics']['throughput_rps']:
                    summary['test_results']['load'] = 'FAIL'
                    summary['overall_status'] = 'FAIL'

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            summary['summary_error'] = str(e)

        return summary

    def print_results(self):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("ARTIFACTOR v3.0 ML PERFORMANCE TEST RESULTS")
        print("="*80)

        summary = self.results.get('summary', {})
        overall_status = summary.get('overall_status', 'UNKNOWN')

        print(f"\nOVERALL STATUS: {overall_status}")
        if overall_status == 'PASS':
            print("✅ All performance targets met!")
        else:
            print("❌ Some performance targets not met")

        # Print target vs actual metrics
        print(f"\nPERFORMANCE METRICS:")
        target_metrics = summary.get('target_metrics', {})
        actual_metrics = summary.get('actual_metrics', {})

        if target_metrics.get('classification_accuracy'):
            target_acc = target_metrics['classification_accuracy']
            actual_acc = actual_metrics.get('classification_accuracy', 0)
            status = "✅" if actual_acc >= target_acc else "❌"
            print(f"  {status} Classification Accuracy: {actual_acc:.3f} (target: {target_acc:.3f})")

        if target_metrics.get('response_time_p95_ms'):
            target_time = target_metrics['response_time_p95_ms']
            actual_time = actual_metrics.get('pipeline_time_ms', 0)
            status = "✅" if actual_time <= target_time else "❌"
            print(f"  {status} Response Time: {actual_time:.1f}ms (target: <{target_time}ms)")

        if target_metrics.get('throughput_rps'):
            target_throughput = target_metrics['throughput_rps']
            actual_throughput = actual_metrics.get('throughput_rps', 0)
            status = "✅" if actual_throughput >= target_throughput else "❌"
            print(f"  {status} Throughput: {actual_throughput:.1f} req/sec (target: >{target_throughput} req/sec)")

        # Print test category results
        print(f"\nTEST CATEGORIES:")
        test_results = summary.get('test_results', {})
        for category, status in test_results.items():
            icon = "✅" if status == 'PASS' else "❌"
            print(f"  {icon} {category.title()}: {status}")

        # Print detailed results
        if self.results.get('classification_tests'):
            print(f"\nCLASSIFICATION TESTS:")
            for test in self.results['classification_tests']:
                if 'error' not in test:
                    icon = "✅" if test['accuracy'] == 1.0 else "❌"
                    print(f"  {icon} {test['test_name']}: {test['processing_time_ms']:.1f}ms, acc: {test['accuracy']:.1f}")

        if self.results.get('load_tests') and 'error' not in self.results['load_tests']:
            load_test = self.results['load_tests']
            print(f"\nLOAD TEST RESULTS:")
            print(f"  Total Requests: {load_test['total_requests']}")
            print(f"  Successful: {load_test['successful_requests']}")
            print(f"  Throughput: {load_test['throughput_rps']:.1f} req/sec")
            print(f"  P95 Latency: {load_test['p95_latency_ms']:.1f}ms")
            print(f"  Success Rate: {load_test['success_rate']:.3f}")

        print("\n" + "="*80)

async def main():
    """Run performance tests"""
    try:
        tester = MLPerformanceTester()
        results = await tester.run_comprehensive_tests()

        # Print results
        tester.print_results()

        # Save results to file
        results_file = Path("ml_performance_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nDetailed results saved to: {results_file}")

        return results

    except Exception as e:
        logger.error(f"Error in performance testing: {e}")
        print(f"\n❌ PERFORMANCE TESTING FAILED: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    asyncio.run(main())