/**
 * Plugin Manager Component
 * Main interface for managing ARTIFACTOR plugins
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
  Tab,
  Tabs,
  Box,
  Alert,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Snackbar
} from '@mui/material';
import {
  GetApp as InstallIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  PlayArrow as EnableIcon,
  Stop as DisableIcon,
  CloudDownload as DownloadIcon,
  Security as SecurityIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  is_enabled: boolean;
  is_system_plugin: boolean;
  installed_at: string;
  config_schema?: any;
  default_config?: any;
}

interface RegistryPlugin {
  name: string;
  version: string;
  description: string;
  author: string;
  download_url: string;
  tags: string[];
  homepage?: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`plugin-tabpanel-${index}`}
      aria-labelledby={`plugin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function PluginManager() {
  const [tabValue, setTabValue] = useState(0);
  const [installedPlugins, setInstalledPlugins] = useState<Plugin[]>([]);
  const [registryPlugins, setRegistryPlugins] = useState<RegistryPlugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState<string | null>(null);

  // Dialog states
  const [settingsDialog, setSettingsDialog] = useState<Plugin | null>(null);
  const [installDialog, setInstallDialog] = useState(false);
  const [pluginFile, setPluginFile] = useState<File | null>(null);
  const [pluginUrl, setPluginUrl] = useState('');

  // Notification state
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  useEffect(() => {
    loadPlugins();
  }, []);

  const loadPlugins = async () => {
    try {
      setLoading(true);

      // Load installed plugins
      const installedResponse = await fetch('/api/plugins/');
      const installedData = await installedResponse.json();

      if (installedData.success) {
        setInstalledPlugins(installedData.plugins);
      }

      // Load registry plugins
      const registryResponse = await fetch('/api/plugins/registry');
      const registryData = await registryResponse.json();

      if (registryData.success) {
        setRegistryPlugins(registryData.plugins);
      }

    } catch (error) {
      console.error('Error loading plugins:', error);
      showNotification('Error loading plugins', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setNotification({ open: true, message, severity });
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const enablePlugin = async (pluginName: string) => {
    try {
      const response = await fetch(`/api/plugins/${pluginName}/enable`, {
        method: 'POST'
      });
      const data = await response.json();

      if (data.success) {
        showNotification(`Plugin ${pluginName} enabled`, 'success');
        loadPlugins();
      } else {
        showNotification(data.error || 'Failed to enable plugin', 'error');
      }
    } catch (error) {
      showNotification('Error enabling plugin', 'error');
    }
  };

  const disablePlugin = async (pluginName: string) => {
    try {
      const response = await fetch(`/api/plugins/${pluginName}/disable`, {
        method: 'POST'
      });
      const data = await response.json();

      if (data.success) {
        showNotification(`Plugin ${pluginName} disabled`, 'success');
        loadPlugins();
      } else {
        showNotification(data.error || 'Failed to disable plugin', 'error');
      }
    } catch (error) {
      showNotification('Error disabling plugin', 'error');
    }
  };

  const uninstallPlugin = async (pluginName: string) => {
    if (!confirm(`Are you sure you want to uninstall ${pluginName}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/plugins/${pluginName}`, {
        method: 'DELETE'
      });
      const data = await response.json();

      if (data.success) {
        showNotification(`Plugin ${pluginName} uninstalled`, 'success');
        loadPlugins();
      } else {
        showNotification(data.error || 'Failed to uninstall plugin', 'error');
      }
    } catch (error) {
      showNotification('Error uninstalling plugin', 'error');
    }
  };

  const installPlugin = async (source: { type: 'file' | 'url' | 'registry'; value: string | File }) => {
    try {
      setInstalling(typeof source.value === 'string' ? source.value : 'file');

      const formData = new FormData();

      if (source.type === 'file' && source.value instanceof File) {
        formData.append('plugin_file', source.value);
      } else if (source.type === 'url') {
        formData.append('plugin_url', source.value as string);
      } else if (source.type === 'registry') {
        formData.append('plugin_name', source.value as string);
      }

      const response = await fetch('/api/plugins/install', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      if (data.success) {
        showNotification('Plugin installation started', 'success');
        setInstallDialog(false);
        setPluginFile(null);
        setPluginUrl('');
        // Reload plugins after a delay to allow installation to complete
        setTimeout(loadPlugins, 2000);
      } else {
        showNotification(data.error || 'Failed to install plugin', 'error');
      }
    } catch (error) {
      showNotification('Error installing plugin', 'error');
    } finally {
      setInstalling(null);
    }
  };

  const installFromRegistry = (plugin: RegistryPlugin) => {
    installPlugin({ type: 'registry', value: plugin.name });
  };

  const renderInstalledPlugins = () => (
    <Grid container spacing={3}>
      {installedPlugins.map((plugin) => (
        <Grid item xs={12} md={6} lg={4} key={plugin.id}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="start">
                <Typography variant="h6" component="h2">
                  {plugin.name}
                </Typography>
                <Chip
                  label={plugin.is_enabled ? 'Enabled' : 'Disabled'}
                  color={plugin.is_enabled ? 'success' : 'default'}
                  size="small"
                />
              </Box>

              <Typography color="textSecondary" gutterBottom>
                v{plugin.version} by {plugin.author}
              </Typography>

              <Typography variant="body2" component="p">
                {plugin.description}
              </Typography>

              <Box mt={2}>
                <Typography variant="caption" color="textSecondary">
                  Installed: {new Date(plugin.installed_at).toLocaleDateString()}
                </Typography>
              </Box>

              {plugin.is_system_plugin && (
                <Chip label="System Plugin" size="small" sx={{ mt: 1 }} />
              )}
            </CardContent>

            <CardActions>
              {plugin.is_enabled ? (
                <Button
                  size="small"
                  startIcon={<DisableIcon />}
                  onClick={() => disablePlugin(plugin.name)}
                  disabled={plugin.is_system_plugin}
                >
                  Disable
                </Button>
              ) : (
                <Button
                  size="small"
                  startIcon={<EnableIcon />}
                  onClick={() => enablePlugin(plugin.name)}
                >
                  Enable
                </Button>
              )}

              <Button
                size="small"
                startIcon={<SettingsIcon />}
                onClick={() => setSettingsDialog(plugin)}
              >
                Settings
              </Button>

              {!plugin.is_system_plugin && (
                <Button
                  size="small"
                  startIcon={<DeleteIcon />}
                  onClick={() => uninstallPlugin(plugin.name)}
                  color="error"
                >
                  Uninstall
                </Button>
              )}
            </CardActions>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const renderRegistryPlugins = () => (
    <Grid container spacing={3}>
      {registryPlugins.map((plugin) => {
        const isInstalled = installedPlugins.some(p => p.name === plugin.name);

        return (
          <Grid item xs={12} md={6} lg={4} key={plugin.name}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h2">
                  {plugin.name}
                </Typography>

                <Typography color="textSecondary" gutterBottom>
                  v{plugin.version} by {plugin.author}
                </Typography>

                <Typography variant="body2" component="p">
                  {plugin.description}
                </Typography>

                <Box mt={2}>
                  {plugin.tags?.map((tag) => (
                    <Chip
                      key={tag}
                      label={tag}
                      size="small"
                      variant="outlined"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  startIcon={<InstallIcon />}
                  onClick={() => installFromRegistry(plugin)}
                  disabled={isInstalled || installing === plugin.name}
                >
                  {isInstalled ? 'Installed' : 'Install'}
                </Button>

                {plugin.homepage && (
                  <Button
                    size="small"
                    startIcon={<InfoIcon />}
                    href={plugin.homepage}
                    target="_blank"
                  >
                    Info
                  </Button>
                )}
              </CardActions>
            </Card>
          </Grid>
        )}
      )}
    </Grid>
  );

  const renderInstallDialog = () => (
    <Dialog open={installDialog} onClose={() => setInstallDialog(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Install Plugin</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Install from file
          </Typography>
          <Button
            variant="outlined"
            component="label"
            fullWidth
            sx={{ mb: 3 }}
          >
            Choose Plugin File (.zip)
            <input
              type="file"
              hidden
              accept=".zip"
              onChange={(e) => setPluginFile(e.target.files?.[0] || null)}
            />
          </Button>

          {pluginFile && (
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Selected: {pluginFile.name}
            </Typography>
          )}

          <Typography variant="subtitle1" gutterBottom>
            Install from URL
          </Typography>
          <TextField
            fullWidth
            label="Plugin URL"
            value={pluginUrl}
            onChange={(e) => setPluginUrl(e.target.value)}
            placeholder="https://github.com/user/plugin/releases/download/v1.0.0/plugin.zip"
            sx={{ mb: 2 }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setInstallDialog(false)}>Cancel</Button>
        <Button
          onClick={() => {
            if (pluginFile) {
              installPlugin({ type: 'file', value: pluginFile });
            } else if (pluginUrl) {
              installPlugin({ type: 'url', value: pluginUrl });
            }
          }}
          disabled={!pluginFile && !pluginUrl}
          variant="contained"
        >
          Install
        </Button>
      </DialogActions>
    </Dialog>
  );

  const renderSettingsDialog = () => (
    <Dialog
      open={!!settingsDialog}
      onClose={() => setSettingsDialog(null)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        Plugin Settings - {settingsDialog?.name}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          Configure settings for {settingsDialog?.name} v{settingsDialog?.version}
        </Typography>

        {/* Plugin-specific settings would be rendered here based on config_schema */}
        <Alert severity="info">
          Plugin-specific configuration interface would be rendered here based on the plugin's configuration schema.
        </Alert>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setSettingsDialog(null)}>Cancel</Button>
        <Button variant="contained">Save Settings</Button>
      </DialogActions>
    </Dialog>
  );

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          Plugin Manager
        </Typography>
        <Button
          variant="contained"
          startIcon={<InstallIcon />}
          onClick={() => setInstallDialog(true)}
        >
          Install Plugin
        </Button>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="plugin manager tabs">
          <Tab label={`Installed (${installedPlugins.length})`} />
          <Tab label={`Registry (${registryPlugins.length})`} />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {installedPlugins.length === 0 ? (
          <Alert severity="info">
            No plugins installed. Browse the registry to install plugins.
          </Alert>
        ) : (
          renderInstalledPlugins()
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {registryPlugins.length === 0 ? (
          <Alert severity="info">
            No plugins available in registry. Check your connection or add plugin registries.
          </Alert>
        ) : (
          renderRegistryPlugins()
        )}
      </TabPanel>

      {renderInstallDialog()}
      {renderSettingsDialog()}

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert
          onClose={() => setNotification({ ...notification, open: false })}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}