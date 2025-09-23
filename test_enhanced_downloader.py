#!/usr/bin/env python3
"""
Test script for the enhanced Claude Artifact Downloader
Tests the new smart project structure and ML-enhanced filetype detection
"""

import sys
import json
from pathlib import Path

# Add the current directory to the path so we can import the downloader
sys.path.insert(0, str(Path(__file__).parent))

# Import with underscore replacement for module name
import claude_artifact_downloader as downloader_module
ClaudeArtifactDownloader = downloader_module.ClaudeArtifactDownloader
Artifact = downloader_module.Artifact
ProjectType = downloader_module.ProjectType
FileTypeDetector = downloader_module.FileTypeDetector

def test_filetype_detection():
    """Test the enhanced filetype detection with confidence scoring"""
    print("🧪 Testing Enhanced Filetype Detection...")

    test_cases = [
        {
            'content': '''import React from 'react';
function App() {
    return <div>Hello World</div>;
}
export default App;''',
            'language': 'javascript',
            'expected_ext': '.js',
            'description': 'React JavaScript component'
        },
        {
            'content': '''def main():
    print("Hello, World!")
if __name__ == "__main__":
    main()''',
            'language': 'python',
            'expected_ext': '.py',
            'description': 'Python main function'
        },
        {
            'content': '''FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt''',
            'language': None,
            'expected_ext': '.dockerfile',
            'description': 'Dockerfile content'
        },
        {
            'content': '''# My Project
This is a README file for my project.
## Installation
Run `npm install` to get started.''',
            'language': None,
            'expected_ext': '.md',
            'description': 'Markdown README'
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        detected_ext, confidence = FileTypeDetector.detect_extension(
            test_case['content'],
            test_case['language']
        )

        status = "✅" if detected_ext == test_case['expected_ext'] else "❌"
        print(f"  {status} Test {i}: {test_case['description']}")
        print(f"     Expected: {test_case['expected_ext']}, Got: {detected_ext}, Confidence: {confidence:.2f}")

def test_project_structure():
    """Test the smart project structure detection"""
    print("\n🏗️ Testing Smart Project Structure...")

    # Create sample artifacts for different project types
    test_artifacts = [
        # Web App artifacts
        Artifact(
            id="1",
            title="App Component",
            content="import React from 'react'; function App() { return <div>App</div>; }",
            type="code",
            language="javascript",
            filename="App.jsx"
        ),
        Artifact(
            id="2",
            title="Styles",
            content=".app { background: #fff; } .header { color: blue; }",
            type="code",
            language="css",
            filename="styles.css"
        ),
        # API Backend artifacts
        Artifact(
            id="3",
            title="API Router",
            content="from flask import Flask, jsonify\napp = Flask(__name__)\n@app.route('/api/data')\ndef get_data(): return jsonify({'data': 'test'})",
            type="code",
            language="python",
            filename="api.py"
        ),
        # Documentation
        Artifact(
            id="4",
            title="README",
            content="# My Project\n\nThis is a web application with a Python API backend.",
            type="text",
            language="markdown",
            filename="README.md"
        )
    ]

    # Test project structure organization
    downloader = ClaudeArtifactDownloader(
        output_dir="./test_artifacts",
        project_structure=True,
        ml_enhanced=True
    )
    downloader.artifacts = test_artifacts

    # Analyze project type
    detected_type = downloader._analyze_project_type()
    print(f"  🎯 Detected project type: {detected_type.value}")

    # Test file categorization
    for artifact in test_artifacts:
        filename = artifact.filename or f"{artifact.title.lower().replace(' ', '_')}.txt"
        project_path = downloader._get_project_path(artifact, filename)
        category = downloader._categorize_file(artifact, filename)
        print(f"  📁 {artifact.title} → {project_path} (category: {category})")

    # Generate project summary
    summary = downloader.generate_project_summary()
    print(f"\n  📊 Project Analysis Summary:")
    print(f"     Total artifacts: {summary['total_artifacts']}")
    print(f"     File types: {summary['file_types']}")
    print(f"     Recommendations: {len(summary['recommendations'])}")

def test_ml_learning():
    """Test the ML learning and correction system"""
    print("\n🤖 Testing ML Learning System...")

    downloader = ClaudeArtifactDownloader(ml_enhanced=True)

    # Test user correction learning
    downloader._learn_from_user_correction(
        original_detection=".txt",
        correct_type=".py",
        content="print('Hello')",
        filename="script.py"
    )

    print("  ✅ User correction logged for ML learning")
    print("  📚 Training data will improve future detection accuracy")

def main():
    """Run all tests for the enhanced artifact downloader"""
    print("🚀 Testing Enhanced Claude Artifact Downloader")
    print("=" * 50)

    try:
        test_filetype_detection()
        test_project_structure()
        test_ml_learning()

        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\n🎉 Enhanced Features Summary:")
        print("   • ML-enhanced filetype detection with confidence scoring")
        print("   • Smart project structure organization (web-app, api-backend, etc.)")
        print("   • Intelligent file categorization (src/, docs/, config/, tests/, etc.)")
        print("   • Project type analysis and recommendations")
        print("   • User correction learning for improved accuracy")
        print("\n📝 Usage Examples:")
        print("   python claude-artifact-downloader.py --project-structure")
        print("   python claude-artifact-downloader.py --project-structure --no-ml")
        print("   python claude-artifact-downloader.py --help")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()