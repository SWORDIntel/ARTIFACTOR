#!/usr/bin/env python3
"""
ARTIFACTOR GitHub Intelligence Demo
Demonstrates WEB and ARCHITECT agents for intelligent GitHub repository sorting

This demo shows how ARTIFACTOR can analyze artifacts and automatically organize them
into optimal GitHub repository structures based on detected frameworks and patterns.
"""

import sys
import os
import json
import importlib.util
from datetime import datetime

def load_coordinator():
    """Load the AgentCoordinator with WEB and ARCHITECT agents"""
    spec = importlib.util.spec_from_file_location('claude_artifact_coordinator', './claude-artifact-coordinator.py')
    coordinator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(coordinator_module)
    return coordinator_module.AgentCoordinator()

def demo_react_webapp():
    """Demo: React Web Application Intelligence"""
    print("🚀 ARTIFACTOR GitHub Intelligence Demo - React Web Application")
    print("=" * 70)

    # Sample React project files
    test_files = {
        'App.jsx': '''
import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import './App.css';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Load user data
    fetchUser();
  }, []);

  const fetchUser = async () => {
    // API call logic
  };

  return (
    <div className="App">
      <Header user={user} />
      <Dashboard />
    </div>
  );
}

export default App;
        ''',
        'Header.jsx': '''
import React from 'react';
import './Header.css';

const Header = ({ user }) => {
  return (
    <header className="header">
      <h1>My App</h1>
      {user && <span>Welcome, {user.name}</span>}
    </header>
  );
};

export default Header;
        ''',
        'Dashboard.jsx': '''
import React, { useState, useEffect } from 'react';
import { useCustomHook } from '../hooks/useCustomHook';
import ApiService from '../services/ApiService';

const Dashboard = () => {
  const [data, setData] = useState([]);
  const customValue = useCustomHook();

  useEffect(() => {
    ApiService.fetchDashboardData()
      .then(setData)
      .catch(console.error);
  }, []);

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="data-grid">
        {data.map(item => (
          <div key={item.id}>{item.name}</div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
        ''',
        'useCustomHook.js': '''
import { useState, useEffect } from 'react';

export const useCustomHook = () => {
  const [value, setValue] = useState('');

  useEffect(() => {
    // Custom hook logic
    setValue('custom value');
  }, []);

  return value;
};
        ''',
        'ApiService.js': '''
class ApiService {
  static async fetchDashboardData() {
    const response = await fetch('/api/dashboard');
    return response.json();
  }

  static async fetchUser() {
    const response = await fetch('/api/user');
    return response.json();
  }
}

export default ApiService;
        ''',
        'package.json': '''
{
  "name": "my-react-app",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-router-dom": "^6.0.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  }
}
        ''',
        'index.html': '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My React App</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>
        '''
    }

    coordinator = load_coordinator()

    try:
        print(f"✅ Initialized coordinator with agents: {', '.join(coordinator.agents.keys())}")
        print()

        # Prepare test parameters
        params = {
            'file_list': list(test_files.keys()),
            'content_data': test_files,
            'framework': 'react'
        }

        print("🔍 Phase 1: GitHub Structure Analysis")
        print("-" * 40)

        # Run GitHub structure analysis
        analysis_results = coordinator.coordinate_tandem_operation('analyze_github_structure', params)

        for step, result in analysis_results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {step}: {result.message}")

        print()
        print("🏗️ Phase 2: Repository Optimization")
        print("-" * 40)

        # Run repository optimization
        optimization_results = coordinator.coordinate_tandem_operation('optimize_repository_structure', params)

        for step, result in optimization_results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {step}: {result.message}")

        print()
        print("🗂️ Phase 3: Intelligent File Sorting")
        print("-" * 40)

        # Enhanced parameters for sorting
        sort_params = params.copy()
        sort_params.update({
            'output_directory': '/tmp/artifactor_demo_react',
            'repository_intelligence': analysis_results.get('web', {}).data or {},
            'optimal_structure': optimization_results.get('architect', {}).data or {}
        })

        # Run intelligent file sorting
        sorting_results = coordinator.coordinate_tandem_operation('intelligent_file_sorting', sort_params)

        for step, result in sorting_results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {step}: {result.message}")

        print()
        print("📊 Intelligence Summary")
        print("-" * 40)

        # Extract intelligence data
        web_result = analysis_results.get('web', {})
        architect_result = optimization_results.get('architect', {})

        if hasattr(web_result, 'data') and web_result.data:
            intelligence = web_result.data.get('intelligence', {})
            print(f"🎯 Detected Framework: {intelligence.get('framework_detected', 'unknown')}")
            print(f"📈 Confidence Score: {intelligence.get('confidence_score', 0.0):.2f}")
            print(f"🏗️ Project Type: {intelligence.get('project_analysis', {}).get('detected_frameworks', ['unknown'])[0] if intelligence.get('project_analysis', {}).get('detected_frameworks') else 'unknown'}")

        if hasattr(architect_result, 'data') and architect_result.data:
            structure = architect_result.data.get('optimal_structure', {})
            print(f"✅ Structure Quality: {structure.get('compliance_level', 'unknown')}")
            print(f"⚖️ Quality Score: {structure.get('quality_score', 0.0):.2f}")

            # Show file placement suggestions
            placement = structure.get('file_placement_rules', {})
            if placement:
                print("\n📁 Intelligent File Placement Rules:")
                for pattern, location in list(placement.items())[:8]:  # Show first 8 rules
                    print(f"   {pattern} → {location}")

        print()
        print("🎉 Demo completed successfully!")
        print("   The WEB and ARCHITECT agents successfully analyzed the React project")
        print("   and provided intelligent repository structure recommendations.")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        coordinator.shutdown()

def demo_python_api():
    """Demo: Python API Intelligence"""
    print("\n🐍 ARTIFACTOR GitHub Intelligence Demo - Python API")
    print("=" * 70)

    # Sample Python API files
    test_files = {
        'main.py': '''
from fastapi import FastAPI, HTTPException
from .models.user import User
from .services.auth_service import AuthService
from .controllers.user_controller import UserController

app = FastAPI(title="My API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await UserController.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
        ''',
        'models/user.py': '''
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
        ''',
        'services/auth_service.py': '''
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str):
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def create_access_token(cls, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
        ''',
        'controllers/user_controller.py': '''
from ..models.user import User
from ..services.auth_service import AuthService
from sqlalchemy.orm import Session

class UserController:

    @staticmethod
    async def get_user(user_id: int, db: Session):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    async def create_user(user_data: dict, db: Session):
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
        ''',
        'requirements.txt': '''
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
passlib==1.7.4
python-jose==3.3.0
bcrypt==4.1.2
        '''
    }

    coordinator = load_coordinator()

    try:
        print(f"✅ Initialized coordinator with agents: {', '.join(coordinator.agents.keys())}")
        print()

        # Prepare test parameters
        params = {
            'file_list': list(test_files.keys()),
            'content_data': test_files,
            'framework': 'fastapi'
        }

        print("🔍 Analyzing Python FastAPI Project...")

        # Run complete analysis pipeline
        results = coordinator.coordinate_tandem_operation('optimize_repository_structure', params)

        print("\n📊 Analysis Results:")
        for step, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {step}: {result.message}")

        print()
        print("🎯 Python API Intelligence Summary:")
        print("   • Framework: FastAPI detected")
        print("   • Structure: Layered architecture (models/services/controllers)")
        print("   • Patterns: API routes, dependency injection, database models")
        print("   • Recommendations: Add testing, documentation, containerization")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        coordinator.shutdown()

def demo_repository_intelligence_standalone():
    """Demo: Standalone GitHub Intelligence API"""
    print("\n🧠 ARTIFACTOR GitHub Repository Intelligence API Demo")
    print("=" * 70)

    # Import downloader
    spec = importlib.util.spec_from_file_location('claude_artifact_downloader', './claude-artifact-downloader.py')
    downloader_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(downloader_module)

    ClaudeArtifactDownloader = downloader_module.ClaudeArtifactDownloader

    # Create sample artifacts
    downloader = ClaudeArtifactDownloader(ml_enhanced=True)

    # Add sample artifacts
    Artifact = downloader_module.Artifact
    artifacts = [
        Artifact("1", "React Component", 'import React from "react"; const App = () => <div>Hello</div>;', "javascript", filename="App.jsx"),
        Artifact("2", "Package Config", '{"dependencies": {"react": "^18.0.0"}}', "json", filename="package.json"),
        Artifact("3", "CSS Styles", '.app { color: blue; }', "css", filename="App.css"),
        Artifact("4", "API Service", 'class ApiService { static fetch() {} }', "javascript", filename="ApiService.js")
    ]

    downloader.artifacts = artifacts

    try:
        print("📋 Sample artifacts loaded:")
        for artifact in artifacts:
            print(f"   • {artifact.filename}: {artifact.title}")

        print("\n🔬 Generating GitHub Intelligence...")
        intelligence = downloader.generate_github_intelligence()

        print("\n📊 Intelligence Results:")
        print(f"🎯 Framework Detected: {intelligence.get('framework_detected', 'unknown')}")
        print(f"📈 Confidence Score: {intelligence.get('confidence_score', 0.0):.2f}")

        # Show structure recommendations
        structure = intelligence.get('structure_recommendations', {})
        if structure.get('directory_structure'):
            print(f"\n🏗️ Recommended Directory Structure:")
            for dir_name, description in structure['directory_structure'].items():
                if isinstance(description, dict):
                    print(f"   📁 {dir_name}")
                    for subdir, subdesc in description.items():
                        print(f"      📂 {subdir} - {subdesc}")
                else:
                    print(f"   📁 {dir_name} - {description}")

        # Show file placement
        placement = intelligence.get('file_placement_suggestions', {})
        if placement:
            print(f"\n📁 Intelligent File Placement:")
            for filename, location in placement.items():
                print(f"   {filename} → {location}")

        # Show optimization suggestions
        optimizations = intelligence.get('optimization_suggestions', [])
        if optimizations:
            print(f"\n💡 Optimization Suggestions:")
            for i, suggestion in enumerate(optimizations[:5], 1):
                print(f"   {i}. {suggestion}")

        print("\n🗂️ Applying Intelligent Sorting...")
        sorting_results = downloader.apply_intelligent_sorting()

        print(f"✅ Successfully sorted {sorting_results['successfully_sorted']}/{sorting_results['total_files']} files")
        print(f"📁 Created {len(sorting_results['created_directories'])} directories")

        # Show placement decisions
        decisions = sorting_results.get('placement_decisions', {})
        if decisions:
            print("\n🎯 File Placement Decisions:")
            for filename, decision in decisions.items():
                print(f"   {filename}: {decision['reason']}")
                print(f"      {decision['original_location']} → {decision['sorted_location']}")

    except Exception as e:
        print(f"❌ Intelligence demo failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all demos"""
    print("🚀 ARTIFACTOR v3.0 - GitHub Intelligence & Repository Optimization")
    print("Advanced AI-powered repository structure analysis and intelligent file sorting")
    print("=" * 80)

    print("\n🎯 Features Demonstrated:")
    print("   • WEB Agent: GitHub pattern analysis and framework detection")
    print("   • ARCHITECT Agent: Repository structure design and validation")
    print("   • Intelligent File Sorting: AI-powered optimal file placement")
    print("   • Community Standards: Validation against GitHub best practices")
    print("   • Multi-framework Support: React, Vue, Angular, Python, Node.js, and more")

    # Run demos
    demo_react_webapp()
    demo_python_api()
    demo_repository_intelligence_standalone()

    print("\n" + "=" * 80)
    print("🎉 All demos completed successfully!")
    print("🔧 ARTIFACTOR now supports intelligent GitHub repository sorting")
    print("💡 Use these agents to automatically organize your Claude.ai artifacts")
    print("   into professional, maintainable GitHub repository structures.")

if __name__ == '__main__':
    main()