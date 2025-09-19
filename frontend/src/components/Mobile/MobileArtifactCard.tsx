import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  IconButton,
  Box,
  Avatar,
  LinearProgress,
  Menu,
  MenuItem,
  useTheme,
  alpha,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  Folder as FolderIcon,
  CloudDownload as CloudDownloadIcon,
  CloudDone as CloudDoneIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useTouchGestures, useSwipeToDismiss } from '../../hooks/useTouchGestures';
import { ProgressiveImage } from './LazyLoadWrapper';
import { format } from 'date-fns';

interface ArtifactCardProps {
  id: string;
  title: string;
  description: string;
  type: string;
  size: number;
  uploadDate: Date;
  tags: string[];
  author: string;
  authorAvatar?: string;
  thumbnailUrl?: string;
  downloadUrl: string;
  isFavorite: boolean;
  isOffline: boolean;
  syncStatus: 'synced' | 'syncing' | 'pending' | 'error';
  onEdit: () => void;
  onDelete: () => void;
  onDownload: () => void;
  onShare: () => void;
  onToggleFavorite: () => void;
  onView: () => void;
}

export const MobileArtifactCard: React.FC<ArtifactCardProps> = ({
  id,
  title,
  description,
  type,
  size,
  uploadDate,
  tags,
  author,
  authorAvatar,
  thumbnailUrl,
  downloadUrl,
  isFavorite,
  isOffline,
  syncStatus,
  onEdit,
  onDelete,
  onDownload,
  onShare,
  onToggleFavorite,
  onView,
}) => {
  const theme = useTheme();
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [isSwipedAway, setIsSwipedAway] = useState(false);

  // Touch gestures
  const touchBind = useTouchGestures({
    onDoubleTap: onToggleFavorite,
    onLongPress: () => setMenuAnchor(document.body), // Show context menu on long press
  });

  const swipeBind = useSwipeToDismiss(() => {
    setIsSwipedAway(true);
    setTimeout(onDelete, 300); // Delay to show animation
  });

  const formatFileSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
  };

  const getTypeColor = (fileType: string): string => {
    const typeColors: Record<string, string> = {
      image: theme.palette.success.main,
      video: theme.palette.error.main,
      audio: theme.palette.warning.main,
      document: theme.palette.info.main,
      code: theme.palette.secondary.main,
      archive: theme.palette.grey[600],
    };
    return typeColors[fileType.toLowerCase()] || theme.palette.primary.main;
  };

  const getSyncIcon = () => {
    switch (syncStatus) {
      case 'synced':
        return <CloudDoneIcon fontSize="small" color="success" />;
      case 'syncing':
        return <CloudDownloadIcon fontSize="small" color="primary" />;
      case 'pending':
        return <CloudDownloadIcon fontSize="small" color="warning" />;
      case 'error':
        return <CloudDownloadIcon fontSize="small" color="error" />;
      default:
        return null;
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleMenuAction = (action: () => void) => {
    action();
    handleMenuClose();
  };

  if (isSwipedAway) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 1, x: 0 }}
      animate={{ opacity: isSwipedAway ? 0 : 1, x: isSwipedAway ? -300 : 0 }}
      transition={{ duration: 0.3 }}
      {...touchBind()}
      {...swipeBind()}
    >
      <Card
        elevation={2}
        onClick={onView}
        sx={{
          mb: 2,
          borderRadius: 3,
          overflow: 'hidden',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            elevation: 4,
            transform: 'translateY(-2px)',
          },
          '&:active': {
            transform: 'scale(0.98)',
          },
          border: isFavorite ? `2px solid ${theme.palette.error.main}` : 'none',
          backgroundColor: isOffline ? alpha(theme.palette.grey[100], 0.7) : 'white',
        }}
      >
        {/* Thumbnail */}
        {thumbnailUrl && (
          <Box sx={{ position: 'relative', height: 120 }}>
            <ProgressiveImage
              src={thumbnailUrl}
              alt={title}
              style={{ height: '100%' }}
            />

            {/* Overlay with sync status */}
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                display: 'flex',
                gap: 0.5,
              }}
            >
              {getSyncIcon()}
              {isFavorite && (
                <FavoriteIcon fontSize="small" sx={{ color: 'white' }} />
              )}
            </Box>

            {/* Type indicator */}
            <Chip
              label={type.toUpperCase()}
              size="small"
              sx={{
                position: 'absolute',
                bottom: 8,
                left: 8,
                backgroundColor: getTypeColor(type),
                color: 'white',
                fontWeight: 'bold',
                fontSize: '0.7rem',
              }}
            />
          </Box>
        )}

        <CardContent sx={{ p: 2, pb: 1 }}>
          {/* Title and Menu */}
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
            <Typography
              variant="subtitle1"
              component="h3"
              sx={{
                flex: 1,
                fontWeight: 600,
                fontSize: '0.95rem',
                lineHeight: 1.3,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {title}
            </Typography>
            <IconButton
              size="small"
              onClick={handleMenuOpen}
              sx={{ ml: 1, p: 0.5 }}
            >
              <MoreVertIcon fontSize="small" />
            </IconButton>
          </Box>

          {/* Description */}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mb: 1.5,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              fontSize: '0.8rem',
              lineHeight: 1.4,
            }}
          >
            {description}
          </Typography>

          {/* Tags */}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1.5 }}>
            {tags.slice(0, 3).map((tag, index) => (
              <Chip
                key={index}
                label={tag}
                size="small"
                variant="outlined"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  '& .MuiChip-label': { px: 1 },
                }}
              />
            ))}
            {tags.length > 3 && (
              <Chip
                label={`+${tags.length - 3}`}
                size="small"
                variant="outlined"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  '& .MuiChip-label': { px: 1 },
                }}
              />
            )}
          </Box>

          {/* Author and Metadata */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar
                src={authorAvatar}
                sx={{ width: 24, height: 24, fontSize: '0.7rem' }}
              >
                {author.charAt(0).toUpperCase()}
              </Avatar>
              <Box>
                <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                  {author}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.65rem' }}>
                  {format(uploadDate, 'MMM d, yyyy')}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                {formatFileSize(size)}
              </Typography>
              {isOffline && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.65rem' }}>
                  Offline
                </Typography>
              )}
            </Box>
          </Box>

          {/* Sync Progress */}
          {syncStatus === 'syncing' && (
            <Box sx={{ mt: 1 }}>
              <LinearProgress size="small" />
            </Box>
          )}
        </CardContent>

        {/* Quick Actions */}
        <CardActions sx={{ p: 1, pt: 0, justifyContent: 'space-between' }}>
          <Box>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite();
              }}
              sx={{ color: isFavorite ? 'error.main' : 'text.secondary' }}
            >
              {isFavorite ? <FavoriteIcon fontSize="small" /> : <FavoriteBorderIcon fontSize="small" />}
            </IconButton>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onShare();
              }}
              sx={{ color: 'text.secondary' }}
            >
              <ShareIcon fontSize="small" />
            </IconButton>
          </Box>

          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onDownload();
            }}
            sx={{
              backgroundColor: theme.palette.primary.main,
              color: 'white',
              '&:hover': {
                backgroundColor: theme.palette.primary.dark,
              },
            }}
          >
            <DownloadIcon fontSize="small" />
          </IconButton>
        </CardActions>

        {/* Context Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem onClick={() => handleMenuAction(onView)}>
            <FolderIcon fontSize="small" sx={{ mr: 1 }} />
            View Details
          </MenuItem>
          <MenuItem onClick={() => handleMenuAction(onEdit)}>
            <EditIcon fontSize="small" sx={{ mr: 1 }} />
            Edit
          </MenuItem>
          <MenuItem onClick={() => handleMenuAction(onShare)}>
            <ShareIcon fontSize="small" sx={{ mr: 1 }} />
            Share
          </MenuItem>
          <MenuItem onClick={() => handleMenuAction(onDownload)}>
            <DownloadIcon fontSize="small" sx={{ mr: 1 }} />
            Download
          </MenuItem>
          <MenuItem onClick={() => handleMenuAction(onDelete)} sx={{ color: 'error.main' }}>
            <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
            Delete
          </MenuItem>
        </Menu>
      </Card>
    </motion.div>
  );
};