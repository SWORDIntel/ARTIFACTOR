import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  Avatar,
  Rating,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Extension as ExtensionIcon,
  Download as DownloadIcon,
  Star as StarIcon,
  Verified as VerifiedIcon,
} from '@mui/icons-material';

const PluginMarketplace: React.FC = () => {
  const theme = useTheme();

  const mockPlugins = [
    {
      id: '1',
      name: 'GitHub Integration',
      description: 'Seamlessly sync artifacts with GitHub repositories',
      author: 'ARTIFACTOR Team',
      rating: 4.8,
      downloads: 1247,
      price: 0,
      verified: true,
      installed: false,
      category: 'Integration',
      tags: ['GitHub', 'Version Control', 'Sync'],
    },
    {
      id: '2',
      name: 'Code Analyzer Pro',
      description: 'Advanced code analysis with complexity metrics',
      author: 'DevTools Inc',
      rating: 4.6,
      downloads: 892,
      price: 9.99,
      verified: true,
      installed: true,
      category: 'Analysis',
      tags: ['Code Analysis', 'Metrics', 'Quality'],
    },
    {
      id: '3',
      name: 'Dark Theme Studio',
      description: 'Beautiful dark themes for all your artifacts',
      author: 'Theme Masters',
      rating: 4.9,
      downloads: 2156,
      price: 4.99,
      verified: false,
      installed: false,
      category: 'UI/UX',
      tags: ['Themes', 'Dark Mode', 'UI'],
    },
  ];

  const PluginCard: React.FC<{ plugin: any }> = ({ plugin }) => (
    <Card
      sx={{
        background: alpha(theme.palette.background.paper, 0.8),
        backdropFilter: 'blur(20px)',
        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        borderRadius: '16px',
        transition: 'all 0.3s ease-in-out',
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
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
          <Avatar
            sx={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              width: 48,
              height: 48,
            }}
          >
            <ExtensionIcon />
          </Avatar>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }} noWrap>
                {plugin.name}
              </Typography>
              {plugin.verified && (
                <VerifiedIcon
                  sx={{ fontSize: 18, color: theme.palette.primary.main }}
                />
              )}
            </Box>
            <Typography variant="body2" color="text.secondary">
              by {plugin.author}
            </Typography>
          </Box>
        </Box>

        {/* Description */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            flex: 1,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {plugin.description}
        </Typography>

        {/* Tags */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {plugin.tags.slice(0, 2).map((tag: string) => (
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
          <Chip
            label={plugin.category}
            size="small"
            variant="outlined"
            sx={{ fontSize: '0.75rem' }}
          />
        </Box>

        {/* Rating and Downloads */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Rating value={plugin.rating} precision={0.1} size="small" readOnly />
            <Typography variant="caption" color="text.secondary">
              {plugin.rating}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <DownloadIcon fontSize="small" color="action" />
            <Typography variant="caption">{plugin.downloads}</Typography>
          </Box>
        </Box>

        {/* Price and Action */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
            {plugin.price === 0 ? 'Free' : `$${plugin.price}`}
          </Typography>
          <Button
            variant={plugin.installed ? 'outlined' : 'contained'}
            size="small"
            disabled={plugin.installed}
            sx={{
              borderRadius: '8px',
              textTransform: 'none',
              fontWeight: 600,
              ...(plugin.installed
                ? {
                    color: theme.palette.success.main,
                    borderColor: theme.palette.success.main,
                  }
                : {
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  }),
            }}
          >
            {plugin.installed ? 'Installed' : 'Install'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
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
        Plugin Marketplace
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Extend ARTIFACTOR with powerful plugins and integrations
      </Typography>

      {/* Featured Plugins */}
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
        Featured Plugins
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {mockPlugins.map((plugin) => (
          <Grid item xs={12} sm={6} md={4} key={plugin.id}>
            <PluginCard plugin={plugin} />
          </Grid>
        ))}
      </Grid>

      {/* Categories */}
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
        Browse by Category
      </Typography>
      
      <Grid container spacing={2}>
        {['Integration', 'Analysis', 'UI/UX', 'Security', 'Performance', 'Automation'].map((category) => (
          <Grid item xs={6} sm={4} md={2} key={category}>
            <Card
              sx={{
                background: alpha(theme.palette.background.paper, 0.6),
                backdropFilter: 'blur(10px)',
                border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  background: alpha(theme.palette.primary.main, 0.1),
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                },
              }}
            >
              <CardContent sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {category}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default PluginMarketplace;