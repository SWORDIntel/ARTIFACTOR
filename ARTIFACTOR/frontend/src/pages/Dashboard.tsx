import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Avatar,
  Chip,
  IconButton,
  Button,
  LinearProgress,
  Tooltip,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Add as AddIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Group as GroupIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  CloudUpload as CloudUploadIcon,
  Search as SearchIcon,
  Extension as ExtensionIcon,
  Star as StarIcon,
  AccessTime as AccessTimeIcon,
  Visibility as VisibilityIcon,
  Comment as CommentIcon,
  Share as ShareIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState, AppDispatch } from '../store/store';
import { fetchArtifacts } from '../store/slices/artifactsSlice';
import { Artifact, ArtifactType } from '../types';

// Mock data for demo purposes
const mockStats = {
  totalArtifacts: 247,
  activeCollaborators: 23,
  mlAccuracy: 87.3,
  storageUsed: 45.2,
  weeklyGrowth: 12.5,
  popularTags: ['React', 'TypeScript', 'Python', 'AI/ML', 'API'],
  recentActivity: 156,
};

const mockRecentArtifacts = [
  {
    id: '1',
    title: 'Advanced React Dashboard Components',
    description: 'Enterprise-grade dashboard components with dark theme support',
    type: ArtifactType.CODE,
    category: 'Frontend',
    tags: ['React', 'TypeScript', 'Material-UI'],
    createdAt: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
    createdBy: 'john.doe',
    collaborators: [],
    isPublic: true,
    classification: {
      primaryCategory: 'Frontend Development',
      confidence: 0.94,
      categories: [],
      keywords: ['react', 'dashboard', 'components'],
      sentiment: { positive: 0.8, neutral: 0.2, negative: 0, overall: 'positive' as const },
      complexity: { score: 7, level: 'medium' as const },
      lastClassified: new Date(),
    },
    metadata: {
      language: 'TypeScript',
      framework: 'React',
      difficulty: 'intermediate' as const,
    },
    views: 342,
    comments: 12,
    stars: 28,
  },
  // Add more mock artifacts...
];

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();

  const { artifacts, isLoading } = useSelector((state: RootState) => state.artifacts);
  const { user } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    dispatch(fetchArtifacts({ page: 1, limit: 10 }));
  }, [dispatch]);

  // Quick action handlers
  const handleCreateArtifact = () => navigate('/artifacts?action=create');
  const handleViewArtifacts = () => navigate('/artifacts');
  const handleMLClassification = () => navigate('/ml-classification');
  const handleCollaboration = () => navigate('/collaboration');
  const handleSearch = () => navigate('/search');
  const handlePlugins = () => navigate('/plugins');

  // Stunning gradient card component
  const GradientCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    gradient: string;
    action?: () => void;
  }> = ({ title, value, subtitle, icon, gradient, action }) => (
    <Card
      sx={{
        background: `linear-gradient(135deg, ${gradient})`,
        border: 'none',
        borderRadius: '16px',
        overflow: 'hidden',
        cursor: action ? 'pointer' : 'default',
        transition: 'all 0.3s ease-in-out',
        '&:hover': action ? {
          transform: 'translateY(-4px)',
          boxShadow: '0 16px 40px rgba(99, 102, 241, 0.3)',
        } : {},
      }}
      onClick={action}
    >
      <CardContent sx={{ p: 3, color: 'white' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {value}
            </Typography>
            <Typography variant="h6" sx={{ opacity: 0.9, fontWeight: 500 }}>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" sx={{ opacity: 0.7, mt: 0.5 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: '12px',
              backgroundColor: alpha('#ffffff', 0.2),
              backdropFilter: 'blur(10px)',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  // Beautiful artifact card
  const ArtifactCard: React.FC<{ artifact: any }> = ({ artifact }) => (
    <Card
      sx={{
        background: alpha(theme.palette.background.paper, 0.8),
        backdropFilter: 'blur(20px)',
        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        borderRadius: '12px',
        transition: 'all 0.3s ease-in-out',
        cursor: 'pointer',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 12px 40px rgba(99, 102, 241, 0.2)',
          border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
        },
      }}
      onClick={() => navigate(`/artifacts/${artifact.id}`)}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
          <Avatar
            sx={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              width: 48,
              height: 48,
            }}
          >
            {artifact.title[0].toUpperCase()}
          </Avatar>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }} noWrap>
              {artifact.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {artifact.description}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {artifact.tags.slice(0, 3).map((tag: string) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  sx={{
                    background: alpha(theme.palette.primary.main, 0.1),
                    color: theme.palette.primary.main,
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                  }}
                />
              ))}
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Tooltip title="Views">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <VisibilityIcon fontSize="small" color="action" />
                <Typography variant="caption">{artifact.views}</Typography>
              </Box>
            </Tooltip>
            <Tooltip title="Comments">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <CommentIcon fontSize="small" color="action" />
                <Typography variant="caption">{artifact.comments}</Typography>
              </Box>
            </Tooltip>
            <Tooltip title="Stars">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <StarIcon fontSize="small" color="action" />
                <Typography variant="caption">{artifact.stars}</Typography>
              </Box>
            </Tooltip>
          </Box>
          <Typography variant="caption" color="text.secondary">
            {new Date(artifact.updatedAt).toLocaleDateString()}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ p: 0 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h3"
          sx={{
            fontWeight: 700,
            mb: 1,
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Welcome back, {user?.name || 'User'}!
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Here's what's happening in your ARTIFACTOR workspace
        </Typography>

        {/* Quick Actions */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateArtifact}
            sx={{
              borderRadius: '10px',
              px: 3,
              py: 1.5,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)',
            }}
          >
            Create Artifact
          </Button>
          <Button
            variant="outlined"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            sx={{ borderRadius: '10px', px: 3, py: 1.5 }}
          >
            Search
          </Button>
          <Button
            variant="outlined"
            startIcon={<ExtensionIcon />}
            onClick={handlePlugins}
            sx={{ borderRadius: '10px', px: 3, py: 1.5 }}
          >
            Plugins
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <GradientCard
            title="Total Artifacts"
            value={mockStats.totalArtifacts}
            subtitle={`+${mockStats.weeklyGrowth}% this week`}
            icon={<StorageIcon />}
            gradient="rgba(99, 102, 241, 0.8), rgba(139, 92, 246, 0.9)"
            action={handleViewArtifacts}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <GradientCard
            title="Active Collaborators"
            value={mockStats.activeCollaborators}
            subtitle="Online now"
            icon={<GroupIcon />}
            gradient="rgba(139, 92, 246, 0.8), rgba(192, 132, 252, 0.9)"
            action={handleCollaboration}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <GradientCard
            title="ML Accuracy"
            value={`${mockStats.mlAccuracy}%`}
            subtitle="Classification model"
            icon={<PsychologyIcon />}
            gradient="rgba(192, 132, 252, 0.8), rgba(168, 85, 247, 0.9)"
            action={handleMLClassification}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <GradientCard
            title="Storage Used"
            value={`${mockStats.storageUsed}%`}
            subtitle="of 100GB plan"
            icon={<CloudUploadIcon />}
            gradient="rgba(168, 85, 247, 0.8), rgba(147, 51, 234, 0.9)"
          />
        </Grid>
      </Grid>

      {/* Recent Activity & Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card
            sx={{
              background: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              borderRadius: '16px',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
                Recent Artifacts
              </Typography>

              {isLoading ? (
                <Box sx={{ mb: 2 }}>
                  <LinearProgress sx={{ borderRadius: '4px', mb: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    Loading your artifacts...
                  </Typography>
                </Box>
              ) : (
                <Grid container spacing={2}>
                  {mockRecentArtifacts.slice(0, 4).map((artifact) => (
                    <Grid item xs={12} sm={6} key={artifact.id}>
                      <ArtifactCard artifact={artifact} />
                    </Grid>
                  ))}
                </Grid>
              )}

              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Button
                  variant="outlined"
                  onClick={handleViewArtifacts}
                  sx={{ borderRadius: '8px' }}
                >
                  View All Artifacts
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              borderRadius: '16px',
              mb: 3,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Popular Tags
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {mockStats.popularTags.map((tag, index) => (
                  <Chip
                    key={tag}
                    label={tag}
                    sx={{
                      background: `linear-gradient(135deg, ${theme.palette.primary.main}${Math.floor(0.8 - index * 0.1)}, ${theme.palette.secondary.main}${Math.floor(0.6 - index * 0.05)})`,
                      color: 'white',
                      fontWeight: 500,
                    }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          <Card
            sx={{
              background: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              borderRadius: '16px',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                System Health
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">API Response</Typography>
                  <Typography variant="body2" color="success.main">145ms</Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={85}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(90deg, #10b981, #06b6d4)',
                      borderRadius: 3,
                    },
                  }}
                />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">ML Processing</Typography>
                  <Typography variant="body2" color="success.main">Active</Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={92}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                      borderRadius: 3,
                    },
                  }}
                />
              </Box>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Database</Typography>
                  <Typography variant="body2" color="success.main">Optimal</Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={96}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(90deg, #8b5cf6, #c084fc)',
                      borderRadius: 3,
                    },
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;