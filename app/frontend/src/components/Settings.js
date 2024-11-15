import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Switch,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Upload as UploadIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

export default function Settings() {
  const { user, changePassword } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Dialog states
  const [openUserDialog, setOpenUserDialog] = useState(false);
  const [openPasswordDialog, setOpenPasswordDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  // Form states
  const [username, setUsername] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    if (user?.is_admin) {
      fetchUsers();
    }
  }, [user]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/admin/users');
      setUsers(response.data.users);
      setLoading(false);
    } catch (error) {
      setError('Failed to fetch users');
      setLoading(false);
    }
  };

  const handleUserSubmit = async () => {
    try {
      if (selectedUser) {
        await axios.put(`/api/admin/users/${selectedUser.id}`, {
          username,
          is_admin: isAdmin
        });
      } else {
        await axios.post('/api/admin/users', {
          username,
          is_admin: isAdmin
        });
      }
      setSuccess('User saved successfully');
      setOpenUserDialog(false);
      fetchUsers();
      resetForm();
    } catch (error) {
      setError(error.response?.data?.message || 'Failed to save user');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`/api/admin/users/${userId}`);
        setSuccess('User deleted successfully');
        fetchUsers();
      } catch (error) {
        setError('Failed to delete user');
      }
    }
  };

  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      await changePassword(currentPassword, newPassword);
      setSuccess('Password changed successfully');
      setOpenPasswordDialog(false);
      resetForm();
    } catch (error) {
      setError(error.response?.data?.message || 'Failed to change password');
    }
  };

  const handleBackupDatabase = async () => {
    try {
      const response = await axios.get('/api/admin/backup', {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `nfl_pickems_backup_${new Date().toISOString()}.db`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setError('Failed to backup database');
    }
  };

  const handleRestoreDatabase = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('backup', file);

    try {
      await axios.post('/api/admin/restore', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setSuccess('Database restored successfully');
      fetchUsers();
    } catch (error) {
      setError('Failed to restore database');
    }
  };

  const resetForm = () => {
    setUsername('');
    setIsAdmin(false);
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setSelectedUser(null);
    setError('');
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {/* Password Management Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Password Management
          </Typography>
          <Button
            variant="contained"
            onClick={() => setOpenPasswordDialog(true)}
          >
            Change Password
          </Button>
        </CardContent>
      </Card>

      {/* Admin Sections */}
      {user?.is_admin && (
        <>
          {/* User Management Section */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  User Management
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => {
                    resetForm();
                    setOpenUserDialog(true);
                  }}
                >
                  Add User
                </Button>
              </Box>
              <List>
                {users.map((user) => (
                  <React.Fragment key={user.id}>
                    <ListItem>
                      <ListItemText
                        primary={user.username}
                        secondary={user.is_admin ? 'Admin' : 'User'}
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setSelectedUser(user);
                            setUsername(user.username);
                            setIsAdmin(user.is_admin);
                            setOpenUserDialog(true);
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          edge="end"
                          onClick={() => handleDeleteUser(user.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Database Management Section */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Database Management
              </Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={handleBackupDatabase}
                >
                  Backup Database
                </Button>
                <Button
                  variant="contained"
                  startIcon={<UploadIcon />}
                  component="label"
                >
                  Restore Database
                  <input
                    type="file"
                    hidden
                    accept=".db"
                    onChange={handleRestoreDatabase}
                  />
                </Button>
              </Box>
            </CardContent>
          </Card>
        </>
      )}

      {/* User Dialog */}
      <Dialog open={openUserDialog} onClose={() => setOpenUserDialog(false)}>
        <DialogTitle>
          {selectedUser ? 'Edit User' : 'Add User'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Username"
            fullWidth
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <Box sx={{ mt: 2 }}>
            <Typography component="label" sx={{ mr: 1 }}>
              Admin Access
            </Typography>
            <Switch
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUserDialog(false)}>Cancel</Button>
          <Button onClick={handleUserSubmit} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Password Dialog */}
      <Dialog open={openPasswordDialog} onClose={() => setOpenPasswordDialog(false)}>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Current Password"
            type="password"
            fullWidth
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
          <TextField
            margin="dense"
            label="New Password"
            type="password"
            fullWidth
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Confirm New Password"
            type="password"
            fullWidth
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPasswordDialog(false)}>Cancel</Button>
          <Button onClick={handlePasswordChange} variant="contained">
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
