/**
 * Plugin Developer Component
 * Tools and utilities for plugin development and testing
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  Alert,
  CircularProgress,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper
} from '@mui/material';
import {
  Code as CodeIcon,
  Build as BuildIcon,
  BugReport as TestIcon,
  CloudDownload as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface PluginTemplate {
  name: string;
  description: string;
  category: string;
  complexity: 'beginner' | 'intermediate' | 'advanced';
  features: string[];
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  info: string[];
  security?: {
    safe: boolean;
    issues: any[];
    warnings: any[];
  };
}

const pluginTemplates: PluginTemplate[] = [
  {
    name: 'Basic Plugin',
    description: 'Simple plugin template with minimal functionality',
    category: 'utility',
    complexity: 'beginner',
    features: ['basic_api', 'configuration']
  },
  {
    name: 'GitHub Integration',
    description: 'Plugin for GitHub repository integration',
    category: 'integration',
    complexity: 'intermediate',
    features: ['network_access', 'api_integration', 'webhooks', 'ui_components']
  },
  {
    name: 'Data Processor',
    description: 'Plugin for data processing and transformation',
    category: 'data',
    complexity: 'intermediate',
    features: ['data_processing', 'file_access', 'database_integration']
  },
  {
    name: 'UI Extension',
    description: 'Plugin that extends the ARTIFACTOR user interface',
    category: 'ui',
    complexity: 'advanced',
    features: ['ui_components', 'react_integration', 'real_time_updates']
  },
  {
    name: 'Agent Integration',
    description: 'Plugin that integrates with ARTIFACTOR agents',
    category: 'agent',
    complexity: 'advanced',
    features: ['agent_coordination', 'async_processing', 'performance_monitoring']
  }
];

const steps = [
  'Choose Template',
  'Configure Plugin',
  'Generate Code',
  'Test & Validate',
  'Package & Distribute'
];

export default function PluginDeveloper() {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState<PluginTemplate | null>(null);
  const [pluginConfig, setPluginConfig] = useState({
    name: '',
    version: '1.0.0',
    description: '',
    author: '',
    license: 'MIT',
    permissions: [] as string[],
    dependencies: [] as string[],
    python_requirements: [] as string[],
    sandbox_mode: true,
    network_access: false,
    agent_integration: false
  });
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setSelectedTemplate(null);
    setPluginConfig({
      name: '',
      version: '1.0.0',
      description: '',
      author: '',
      license: 'MIT',
      permissions: [],
      dependencies: [],
      python_requirements: [],
      sandbox_mode: true,
      network_access: false,
      agent_integration: false
    });
    setValidationResult(null);
    setGeneratedCode(null);
  };

  const selectTemplate = (template: PluginTemplate) => {
    setSelectedTemplate(template);

    // Update config based on template
    setPluginConfig(prev => ({
      ...prev,
      permissions: template.features,
      network_access: template.features.includes('network_access'),
      agent_integration: template.features.includes('agent_coordination')
    }));

    handleNext();
  };

  const generatePlugin = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/plugins/sdk/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          template: selectedTemplate?.name,
          config: pluginConfig
        })
      });

      const data = await response.json();

      if (data.success) {
        setGeneratedCode(data.code);
        handleNext();
      } else {
        console.error('Failed to generate plugin:', data.error);
      }
    } catch (error) {
      console.error('Error generating plugin:', error);
    } finally {
      setLoading(false);
    }
  };

  const validatePlugin = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/plugins/sdk/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config: pluginConfig,
          code: generatedCode
        })
      });

      const data = await response.json();

      if (data.success) {
        setValidationResult(data.validation);
        handleNext();
      } else {
        console.error('Failed to validate plugin:', data.error);
      }
    } catch (error) {
      console.error('Error validating plugin:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadPlugin = async () => {
    try {
      const response = await fetch('/api/plugins/sdk/package', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config: pluginConfig,
          code: generatedCode
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${pluginConfig.name}-${pluginConfig.version}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error downloading plugin:', error);
    }
  };

  const renderTemplateSelection = () => (
    <Grid container spacing={3}>
      {pluginTemplates.map((template) => (
        <Grid item xs={12} md={6} key={template.name}>
          <Card
            sx={{
              cursor: 'pointer',
              '&:hover': { boxShadow: 6 },
              border: selectedTemplate?.name === template.name ? 2 : 0,
              borderColor: 'primary.main'
            }}
            onClick={() => selectTemplate(template)}
          >
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="start">
                <Typography variant="h6" component="h3">
                  {template.name}
                </Typography>
                <Chip
                  label={template.complexity}
                  color={
                    template.complexity === 'beginner' ? 'success' :
                    template.complexity === 'intermediate' ? 'warning' : 'error'
                  }
                  size="small"
                />
              </Box>

              <Typography color="textSecondary" gutterBottom>
                Category: {template.category}
              </Typography>

              <Typography variant="body2" component="p" sx={{ mb: 2 }}>
                {template.description}
              </Typography>

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Features:
                </Typography>
                {template.features.map((feature) => (
                  <Chip
                    key={feature}
                    label={feature}
                    size="small"
                    variant="outlined"
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const renderPluginConfiguration = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>

            <TextField
              fullWidth
              label="Plugin Name"
              value={pluginConfig.name}
              onChange={(e) => setPluginConfig(prev => ({ ...prev, name: e.target.value }))}
              sx={{ mb: 2 }}
              required
            />

            <TextField
              fullWidth
              label="Version"
              value={pluginConfig.version}
              onChange={(e) => setPluginConfig(prev => ({ ...prev, version: e.target.value }))}
              sx={{ mb: 2 }}
              required
            />

            <TextField
              fullWidth
              label="Description"
              value={pluginConfig.description}
              onChange={(e) => setPluginConfig(prev => ({ ...prev, description: e.target.value }))}
              multiline
              rows={3}
              sx={{ mb: 2 }}
              required
            />

            <TextField
              fullWidth
              label="Author"
              value={pluginConfig.author}
              onChange={(e) => setPluginConfig(prev => ({ ...prev, author: e.target.value }))}
              sx={{ mb: 2 }}
              required
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>License</InputLabel>
              <Select
                value={pluginConfig.license}
                onChange={(e) => setPluginConfig(prev => ({ ...prev, license: e.target.value }))}
              >
                <MenuItem value="MIT">MIT</MenuItem>
                <MenuItem value="Apache-2.0">Apache 2.0</MenuItem>
                <MenuItem value="GPL-3.0">GPL 3.0</MenuItem>
                <MenuItem value="BSD-3-Clause">BSD 3-Clause</MenuItem>
                <MenuItem value="Custom">Custom</MenuItem>
              </Select>
            </FormControl>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configuration
            </Typography>

            <TextField
              fullWidth
              label="Permissions (comma-separated)"
              value={pluginConfig.permissions.join(', ')}
              onChange={(e) => setPluginConfig(prev => ({
                ...prev,
                permissions: e.target.value.split(',').map(p => p.trim()).filter(p => p)
              }))}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Dependencies (comma-separated)"
              value={pluginConfig.dependencies.join(', ')}
              onChange={(e) => setPluginConfig(prev => ({
                ...prev,
                dependencies: e.target.value.split(',').map(d => d.trim()).filter(d => d)
              }))}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Python Requirements (comma-separated)"
              value={pluginConfig.python_requirements.join(', ')}
              onChange={(e) => setPluginConfig(prev => ({
                ...prev,
                python_requirements: e.target.value.split(',').map(r => r.trim()).filter(r => r)
              }))}
              sx={{ mb: 2 }}
            />

            <Box sx={{ mb: 2 }}>
              <label>
                <input
                  type="checkbox"
                  checked={pluginConfig.sandbox_mode}
                  onChange={(e) => setPluginConfig(prev => ({ ...prev, sandbox_mode: e.target.checked }))}
                />
                {' '}Sandbox Mode
              </label>
            </Box>

            <Box sx={{ mb: 2 }}>
              <label>
                <input
                  type="checkbox"
                  checked={pluginConfig.network_access}
                  onChange={(e) => setPluginConfig(prev => ({ ...prev, network_access: e.target.checked }))}
                />
                {' '}Network Access
              </label>
            </Box>

            <Box sx={{ mb: 2 }}>
              <label>
                <input
                  type="checkbox"
                  checked={pluginConfig.agent_integration}
                  onChange={(e) => setPluginConfig(prev => ({ ...prev, agent_integration: e.target.checked }))}
                />
                {' '}Agent Integration
              </label>
            </Box>
          </CardContent>
          <CardActions>
            <Button onClick={handleBack}>Back</Button>
            <Button
              variant="contained"
              onClick={generatePlugin}
              disabled={!pluginConfig.name || !pluginConfig.description || !pluginConfig.author || loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Generate Plugin'}
            </Button>
          </CardActions>
        </Card>
      </Grid>
    </Grid>
  );

  const renderGeneratedCode = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Generated Plugin Code
      </Typography>

      <Alert severity="success" sx={{ mb: 2 }}>
        Plugin code generated successfully! Review the code below and proceed to testing.
      </Alert>

      <Paper sx={{ p: 2, mb: 2, maxHeight: 400, overflow: 'auto' }}>
        <pre style={{ margin: 0, fontSize: '0.875rem' }}>
          {generatedCode || 'Loading...'}
        </pre>
      </Paper>

      <Box display="flex" gap={2}>
        <Button onClick={handleBack}>Back</Button>
        <Button variant="contained" onClick={validatePlugin}>
          Test & Validate
        </Button>
      </Box>
    </Box>
  );

  const renderValidationResults = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Validation Results
      </Typography>

      {validationResult && (
        <>
          <Alert
            severity={validationResult.valid ? 'success' : 'error'}
            sx={{ mb: 2 }}
          >
            {validationResult.valid
              ? 'Plugin validation passed! Your plugin is ready for packaging.'
              : 'Plugin validation failed. Please fix the issues below.'}
          </Alert>

          {validationResult.errors.length > 0 && (
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <ErrorIcon color="error" sx={{ mr: 1 }} />
                <Typography>Errors ({validationResult.errors.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {validationResult.errors.map((error, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <ErrorIcon color="error" />
                      </ListItemIcon>
                      <ListItemText primary={error} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}

          {validationResult.warnings.length > 0 && (
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <WarningIcon color="warning" sx={{ mr: 1 }} />
                <Typography>Warnings ({validationResult.warnings.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {validationResult.warnings.map((warning, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <WarningIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText primary={warning} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}

          {validationResult.security && (
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <CheckIcon color={validationResult.security.safe ? 'success' : 'error'} sx={{ mr: 1 }} />
                <Typography>Security Scan</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  {validationResult.security.safe
                    ? 'No security issues detected.'
                    : 'Security issues found. Please review your code.'}
                </Typography>

                {validationResult.security.issues.length > 0 && (
                  <List>
                    {validationResult.security.issues.map((issue, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <ErrorIcon color="error" />
                        </ListItemIcon>
                        <ListItemText
                          primary={issue.pattern}
                          secondary={`File: ${issue.file}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </AccordionDetails>
            </Accordion>
          )}
        </>
      )}

      <Box display="flex" gap={2}>
        <Button onClick={handleBack}>Back</Button>
        {validationResult?.valid && (
          <Button variant="contained" onClick={handleNext}>
            Package Plugin
          </Button>
        )}
      </Box>
    </Box>
  );

  const renderPackaging = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Package & Distribute
      </Typography>

      <Alert severity="success" sx={{ mb: 2 }}>
        Your plugin is ready for packaging and distribution!
      </Alert>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Plugin Summary
          </Typography>
          <Typography><strong>Name:</strong> {pluginConfig.name}</Typography>
          <Typography><strong>Version:</strong> {pluginConfig.version}</Typography>
          <Typography><strong>Author:</strong> {pluginConfig.author}</Typography>
          <Typography><strong>License:</strong> {pluginConfig.license}</Typography>
          <Typography><strong>Template:</strong> {selectedTemplate?.name}</Typography>
        </CardContent>
      </Card>

      <Box display="flex" gap={2}>
        <Button onClick={handleBack}>Back</Button>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={downloadPlugin}
        >
          Download Plugin Package
        </Button>
        <Button onClick={handleReset} color="secondary">
          Create Another Plugin
        </Button>
      </Box>
    </Box>
  );

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return renderTemplateSelection();
      case 1:
        return renderPluginConfiguration();
      case 2:
        return renderGeneratedCode();
      case 3:
        return renderValidationResults();
      case 4:
        return renderPackaging();
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Plugin Developer
      </Typography>

      <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
        Create and develop plugins for ARTIFACTOR using our guided development tools.
      </Typography>

      <Stepper activeStep={activeStep} orientation="vertical">
        {steps.map((label, index) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
            <StepContent>
              {getStepContent(index)}
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {activeStep === steps.length && (
        <Paper square elevation={0} sx={{ p: 3 }}>
          <Typography>All steps completed - plugin development finished!</Typography>
          <Button onClick={handleReset} sx={{ mt: 1, mr: 1 }}>
            Create Another Plugin
          </Button>
        </Paper>
      )}
    </Container>
  );
}