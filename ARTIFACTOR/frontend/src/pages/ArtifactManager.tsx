import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Chip,
  Avatar,
  IconButton,
  Menu,
  MenuItem,
  Fab,
  Tooltip,
  alpha,
  useTheme,
  FormControl,
  Select,
  InputLabel,
  SelectChangeEvent,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  ViewModule as ViewModuleIcon,
  ViewList as ViewListIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Share as ShareIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Visibility as VisibilityIcon,
  Comment as CommentIcon,
  CloudUpload as CloudUploadIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  Image as ImageIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store/store';
import { fetchArtifacts, setFilters } from '../store/slices/artifactsSlice';
import { setCurrentView } from '../store/slices/uiSlice';
import { ViewType, ArtifactType, DifficultyLevel } from '../types';

// Mock data for demonstration
const mockArtifacts = [
  {
    id: '1',
    title: 'Advanced React Dashboard',
    description: 'Enterprise-grade dashboard components with dark theme support and real-time collaboration',
    type: ArtifactType.CODE,
    category: 'Frontend',
    tags: ['React', 'TypeScript', 'Material-UI', 'Dashboard'],
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-01-20'),
    createdBy: 'john.doe',
    views: 342,
    comments: 12,
    stars: 28,
    isStarred: false,
    difficulty: DifficultyLevel.INTERMEDIATE,
    language: 'TypeScript',
  },
  {
    id: '2',
    title: 'ML Classification Pipeline',
    description: 'Complete machine learning pipeline for artifact classification with 87.3% accuracy',
    type: ArtifactType.CODE,
    category: 'Machine Learning',
    tags: ['Python', 'Scikit-learn', 'ML', 'Classification'],
    createdAt: new Date('2024-01-10'),
    updatedAt: new Date('2024-01-18'),
    createdBy: 'jane.smith',
    views: 156,
    comments: 8,
    stars: 15,
    isStarred: true,
    difficulty: DifficultyLevel.ADVANCED,
    language: 'Python',
  },
  // Add more mock artifacts...
];

const ArtifactManager: React.FC = () => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();

  const { artifacts, filters, isLoading } = useSelector((state: RootState) => state.artifacts);
  const { currentView } = useSelector((state: RootState) => state.ui);

  const [searchQuery, setSearchQuery] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);

  useEffect(() => {
    dispatch(fetchArtifacts({ page: 1, limit: 20 }));
  }, [dispatch]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
    dispatch(setFilters({ search: event.target.value }));
  };

  const handleViewChange = (view: ViewType) => {
    dispatch(setCurrentView(view));
  };

  const handleFilterChange = (field: string) => (event: SelectChangeEvent) => {
    dispatch(setFilters({ [field]: event.target.value }));
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, artifactId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedArtifact(artifactId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedArtifact(null);
  };

  const getArtifactIcon = (type: ArtifactType) => {
    switch (type) {
      case ArtifactType.CODE:
        return <CodeIcon />;
      case ArtifactType.DOCUMENTATION:
        return <DescriptionIcon />;
      case ArtifactType.DESIGN:
        return <ImageIcon />;
      default:
        return <DescriptionIcon />;
    }
  };

  const getDifficultyColor = (difficulty: DifficultyLevel) => {
    switch (difficulty) {
      case DifficultyLevel.BEGINNER:
        return theme.palette.success.main;
      case DifficultyLevel.INTERMEDIATE:
        return theme.palette.warning.main;
      case DifficultyLevel.ADVANCED:
        return theme.palette.error.main;
      case DifficultyLevel.EXPERT:
        return theme.palette.secondary.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const ArtifactCard: React.FC<{ artifact: any }> = ({ artifact }) => (
    <Card
      sx={{
        background: alpha(theme.palette.background.paper, 0.8),
        backdropFilter: 'blur(20px)',
        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        borderRadius: '16px',
        transition: 'all 0.3s ease-in-out',
        cursor: 'pointer',
        height: '100%',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 16px 40px rgba(99, 102, 241, 0.2)',
          border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
        },
      }}
    >
      <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Avatar
            sx={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              width: 48,
              height: 48,
            }}
          >
            {getArtifactIcon(artifact.type)}
          </Avatar>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton size="small" sx={{ color: artifact.isStarred ? theme.palette.warning.main : 'inherit' }}>
              {artifact.isStarred ? <StarIcon /> : <StarBorderIcon />}
            </IconButton>
            <IconButton
              size="small"
              onClick={(e) => handleMenuOpen(e, artifact.id)}
            >
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Content */}
        <Box sx={{ flex: 1, mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }} noWrap>
            {artifact.title}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mb: 2,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {artifact.description}
          </Typography>

          {/* Tags */}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            {artifact.tags.slice(0, 3).map((tag: string) => (
              <Chip
                key={tag}
                label={tag}
                size="small"
                sx={{
                  background: alpha(theme.palette.primary.main, 0.1),
                  color: theme.palette.primary.main,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                  fontSize: '0.75rem',
                }}
              />
            ))}
            {artifact.tags.length > 3 && (
              <Chip
                label={`+${artifact.tags.length - 3}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
            )}
          </Box>

          {/* Difficulty & Language */}
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <Chip
              label={artifact.difficulty}
              size="small"
              sx={{
                backgroundColor: alpha(getDifficultyColor(artifact.difficulty), 0.1),
                color: getDifficultyColor(artifact.difficulty),
                border: `1px solid ${alpha(getDifficultyColor(artifact.difficulty), 0.3)}`,
                fontSize: '0.75rem',
              }}
            />
            {artifact.language && (
              <Chip
                label={artifact.language}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
            )}
          </Box>
        </Box>

        {/* Footer */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 1, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
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
            {artifact.updatedAt.toLocaleDateString()}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Artifact Manager
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage and organize your Claude.ai artifacts with enterprise-grade tools
        </Typography>
      </Box>

      {/* Search and Filters */}
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
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search artifacts..."
                value={searchQuery}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '12px',
                  },
                }}
              />
            </Grid>
            <Grid item xs={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={filters.type}
                  label="Type"
                  onChange={handleFilterChange('type')}
                  sx={{ borderRadius: '12px' }}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value={ArtifactType.CODE}>Code</MenuItem>
                  <MenuItem value={ArtifactType.DOCUMENTATION}>Documentation</MenuItem>
                  <MenuItem value={ArtifactType.DESIGN}>Design</MenuItem>
                  <MenuItem value={ArtifactType.DATA}>Data</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Difficulty</InputLabel>
                <Select
                  value={filters.difficulty}
                  label="Difficulty"
                  onChange={handleFilterChange('difficulty')}
                  sx={{ borderRadius: '12px' }}
                >
                  <MenuItem value="all">All Levels</MenuItem>
                  <MenuItem value={DifficultyLevel.BEGINNER}>Beginner</MenuItem>
                  <MenuItem value={DifficultyLevel.INTERMEDIATE}>Intermediate</MenuItem>
                  <MenuItem value={DifficultyLevel.ADVANCED}>Advanced</MenuItem>
                  <MenuItem value={DifficultyLevel.EXPERT}>Expert</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                <Tooltip title="Grid View">
                  <IconButton
                    onClick={() => handleViewChange(ViewType.GRID)}
                    sx={{
                      backgroundColor: currentView === ViewType.GRID ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
                      color: currentView === ViewType.GRID ? theme.palette.primary.main : 'inherit',
                    }}
                  >
                    <ViewModuleIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="List View">
                  <IconButton
                    onClick={() => handleViewChange(ViewType.LIST)}
                    sx={{
                      backgroundColor: currentView === ViewType.LIST ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
                      color: currentView === ViewType.LIST ? theme.palette.primary.main : 'inherit',
                    }}
                  >
                    <ViewListIcon />
                  </IconButton>
                </Tooltip>
                <Button
                  variant="outlined"
                  startIcon={<FilterIcon />}
                  sx={{ borderRadius: '10px', ml: 1 }}
                >
                  Filters
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Artifacts Grid */}
      <Grid container spacing={3}>
        {mockArtifacts.map((artifact) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={artifact.id}>
            <ArtifactCard artifact={artifact} />
          </Grid>
        ))}
      </Grid>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            background: alpha(theme.palette.background.paper, 0.95),
            backdropFilter: 'blur(20px)',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            borderRadius: '12px',
            minWidth: '180px',
          },
        }}
      >
        <MenuItem onClick={handleMenuClose}>
          <EditIcon sx={{ mr: 2 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ShareIcon sx={{ mr: 2 }} />
          Share
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <CloudUploadIcon sx={{ mr: 2 }} />
          Export
        </MenuItem>
        <MenuItem onClick={handleMenuClose} sx={{ color: theme.palette.error.main }}>
          <DeleteIcon sx={{ mr: 2 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          boxShadow: '0 8px 32px rgba(99, 102, 241, 0.3)',
          '&:hover': {
            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
            boxShadow: '0 12px 40px rgba(99, 102, 241, 0.4)',
          },
        }}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default ArtifactManager;