import React, { useState, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  useTheme,
  Alert,
  Fade,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  PhotoCamera as CameraIcon,
  Videocam as VideocamIcon,
  AttachFile as AttachFileIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Mic as MicIcon,
  Stop as StopIcon,
} from '@mui/material/IconButton';
import { motion, AnimatePresence } from 'framer-motion';
import { useTouchGestures } from '../../hooks/useTouchGestures';
import { useOfflineSync } from '../../hooks/useOfflineSync';

interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  thumbnail?: string;
  error?: string;
}

interface MobileUploadProps {
  onUploadComplete: (files: UploadFile[]) => void;
  onUploadProgress: (progress: number) => void;
  maxFileSize?: number; // in MB
  allowedTypes?: string[];
  maxFiles?: number;
}

export const MobileUpload: React.FC<MobileUploadProps> = ({
  onUploadComplete,
  onUploadProgress,
  maxFileSize = 50,
  allowedTypes = ['image/*', 'video/*', 'audio/*', 'application/*'],
  maxFiles = 10,
}) => {
  const theme = useTheme();
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingType, setRecordingType] = useState<'audio' | 'video' | null>(null);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  const { storeOfflineAction, syncStatus } = useOfflineSync();

  // Touch gestures for drag and drop
  const bind = useTouchGestures({
    onLongPress: () => {
      // Trigger file selection on long press
      fileInputRef.current?.click();
    },
  });

  const createThumbnail = useCallback((file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = () => {
          const img = new Image();
          img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // Create thumbnail
            const maxSize = 200;
            const ratio = Math.min(maxSize / img.width, maxSize / img.height);
            canvas.width = img.width * ratio;
            canvas.height = img.height * ratio;

            ctx?.drawImage(img, 0, 0, canvas.width, canvas.height);
            resolve(canvas.toDataURL());
          };
          img.src = reader.result as string;
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      } else {
        // For non-image files, return a default thumbnail
        resolve('');
      }
    });
  }, []);

  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize * 1024 * 1024) {
      return `File size exceeds ${maxFileSize}MB limit`;
    }

    // Check file type
    const isAllowedType = allowedTypes.some(type => {
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type;
    });

    if (!isAllowedType) {
      return 'File type not allowed';
    }

    return null;
  }, [maxFileSize, allowedTypes]);

  const addFiles = useCallback(async (fileList: FileList) => {
    const newFiles: UploadFile[] = [];

    for (let i = 0; i < Math.min(fileList.length, maxFiles - files.length); i++) {
      const file = fileList[i];
      const error = validateFile(file);

      const uploadFile: UploadFile = {
        id: `${Date.now()}-${i}`,
        file,
        progress: 0,
        status: error ? 'error' : 'pending',
        error,
      };

      if (!error) {
        try {
          uploadFile.thumbnail = await createThumbnail(file);
        } catch (err) {
          console.warn('Failed to create thumbnail:', err);
        }
      }

      newFiles.push(uploadFile);
    }

    setFiles(prev => [...prev, ...newFiles]);
  }, [files.length, maxFiles, validateFile, createThumbnail]);

  const uploadFiles = useCallback(async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');

    for (const uploadFile of pendingFiles) {
      try {
        // Update status to uploading
        setFiles(prev => prev.map(f =>
          f.id === uploadFile.id ? { ...f, status: 'uploading' } : f
        ));

        // Create FormData
        const formData = new FormData();
        formData.append('file', uploadFile.file);
        formData.append('title', uploadFile.file.name);
        formData.append('type', uploadFile.file.type);

        // If offline, store for later sync
        if (!syncStatus.isOnline) {
          await storeOfflineAction({
            type: 'upload',
            data: formData,
          });

          // Update status to completed (will sync later)
          setFiles(prev => prev.map(f =>
            f.id === uploadFile.id ? { ...f, status: 'completed', progress: 100 } : f
          ));
          continue;
        }

        // Online upload with progress tracking
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = Math.round((e.loaded / e.total) * 100);
            setFiles(prev => prev.map(f =>
              f.id === uploadFile.id ? { ...f, progress } : f
            ));
            onUploadProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            setFiles(prev => prev.map(f =>
              f.id === uploadFile.id ? { ...f, status: 'completed', progress: 100 } : f
            ));
          } else {
            setFiles(prev => prev.map(f =>
              f.id === uploadFile.id ? {
                ...f,
                status: 'error',
                error: `Upload failed: ${xhr.statusText}`
              } : f
            ));
          }
        });

        xhr.addEventListener('error', () => {
          setFiles(prev => prev.map(f =>
            f.id === uploadFile.id ? {
              ...f,
              status: 'error',
              error: 'Upload failed: Network error'
            } : f
          ));
        });

        xhr.open('POST', '/api/artifacts/upload');
        xhr.send(formData);

      } catch (error) {
        setFiles(prev => prev.map(f =>
          f.id === uploadFile.id ? {
            ...f,
            status: 'error',
            error: `Upload failed: ${error.message}`
          } : f
        ));
      }
    }
  }, [files, storeOfflineAction, syncStatus.isOnline, onUploadProgress]);

  const removeFile = useCallback((fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  }, []);

  const startRecording = useCallback(async (type: 'audio' | 'video') => {
    try {
      const constraints = {
        audio: true,
        video: type === 'video',
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, {
          type: type === 'video' ? 'video/webm' : 'audio/webm'
        });
        const file = new File([blob], `recording-${Date.now()}.webm`, {
          type: blob.type,
        });

        const fileList = new DataTransfer();
        fileList.items.add(file);
        addFiles(fileList.files);

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        setIsRecording(false);
        setRecordingType(null);
        setMediaRecorder(null);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingType(type);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Failed to access camera/microphone');
    }
  }, [addFiles]);

  const stopRecording = useCallback(() => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
  }, [mediaRecorder]);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!dropZoneRef.current?.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      addFiles(droppedFiles);
    }
  }, [addFiles]);

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return '📷';
    if (file.type.startsWith('video/')) return '🎥';
    if (file.type.startsWith('audio/')) return '🎵';
    return '📄';
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'uploading':
        return <CircularProgress size={20} />;
      default:
        return null;
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Upload Area */}
      <Paper
        ref={dropZoneRef}
        elevation={isDragOver ? 8 : 2}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        {...bind()}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          background: isDragOver
            ? `linear-gradient(135deg, ${theme.palette.primary.light}, ${theme.palette.primary.main})`
            : theme.palette.background.paper,
          color: isDragOver ? 'white' : 'inherit',
          border: `2px dashed ${
            isDragOver ? theme.palette.primary.main : theme.palette.grey[300]
          }`,
          borderRadius: 3,
          mb: 3,
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <motion.div
          animate={{ scale: isDragOver ? 1.05 : 1 }}
          transition={{ duration: 0.2 }}
        >
          <UploadIcon
            sx={{
              fontSize: 48,
              mb: 2,
              color: isDragOver ? 'white' : 'primary.main'
            }}
          />
          <Typography variant="h6" gutterBottom>
            {isDragOver ? 'Drop files here' : 'Tap to upload or drag files'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Support for images, videos, documents up to {maxFileSize}MB
          </Typography>
        </motion.div>
      </Paper>

      {/* Quick Action Buttons */}
      <Box sx={{ display: 'flex', gap: 1, mb: 3, overflowX: 'auto', pb: 1 }}>
        <Button
          variant="outlined"
          startIcon={<CameraIcon />}
          onClick={() => cameraInputRef.current?.click()}
          sx={{ minWidth: 120, flexShrink: 0 }}
        >
          Camera
        </Button>

        <Button
          variant="outlined"
          startIcon={<MicIcon />}
          onClick={() => startRecording('audio')}
          disabled={isRecording}
          sx={{ minWidth: 120, flexShrink: 0 }}
        >
          Audio
        </Button>

        <Button
          variant="outlined"
          startIcon={<VideocamIcon />}
          onClick={() => startRecording('video')}
          disabled={isRecording}
          sx={{ minWidth: 120, flexShrink: 0 }}
        >
          Video
        </Button>

        <Button
          variant="outlined"
          startIcon={<AttachFileIcon />}
          onClick={() => fileInputRef.current?.click()}
          sx={{ minWidth: 120, flexShrink: 0 }}
        >
          Files
        </Button>
      </Box>

      {/* Recording Indicator */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Alert
              severity="info"
              sx={{ mb: 2 }}
              action={
                <Button color="inherit" size="small" onClick={stopRecording}>
                  <StopIcon /> Stop
                </Button>
              }
            >
              Recording {recordingType}... Tap stop when finished.
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Offline Status */}
      {!syncStatus.isOnline && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          You're offline. Files will be uploaded when connection is restored.
        </Alert>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Files ({files.length}/{maxFiles})
            </Typography>
            <Button
              variant="contained"
              onClick={uploadFiles}
              disabled={files.every(f => f.status !== 'pending') || isRecording}
            >
              Upload All
            </Button>
          </Box>

          <List>
            <AnimatePresence>
              {files.map((uploadFile, index) => (
                <motion.div
                  key={uploadFile.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <ListItem
                    sx={{
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 2,
                      mb: 1,
                      backgroundColor: 'background.paper',
                    }}
                  >
                    <Box sx={{ mr: 2, fontSize: '1.5em' }}>
                      {uploadFile.thumbnail ? (
                        <img
                          src={uploadFile.thumbnail}
                          alt={uploadFile.file.name}
                          style={{ width: 40, height: 40, borderRadius: 4, objectFit: 'cover' }}
                        />
                      ) : (
                        getFileIcon(uploadFile.file)
                      )}
                    </Box>

                    <ListItemText
                      primary={uploadFile.file.name}
                      secondary={
                        <Box>
                          <Typography variant="caption">
                            {(uploadFile.file.size / 1024 / 1024).toFixed(2)} MB
                          </Typography>
                          {uploadFile.status === 'uploading' && (
                            <LinearProgress
                              variant="determinate"
                              value={uploadFile.progress}
                              sx={{ mt: 1 }}
                            />
                          )}
                          {uploadFile.error && (
                            <Typography variant="caption" color="error">
                              {uploadFile.error}
                            </Typography>
                          )}
                        </Box>
                      }
                    />

                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStatusIcon(uploadFile.status)}
                        <IconButton
                          edge="end"
                          onClick={() => removeFile(uploadFile.id)}
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                </motion.div>
              ))}
            </AnimatePresence>
          </List>
        </Box>
      )}

      {/* Hidden File Inputs */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={allowedTypes.join(',')}
        style={{ display: 'none' }}
        onChange={(e) => e.target.files && addFiles(e.target.files)}
      />

      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*,video/*"
        capture="environment"
        style={{ display: 'none' }}
        onChange={(e) => e.target.files && addFiles(e.target.files)}
      />
    </Box>
  );
};