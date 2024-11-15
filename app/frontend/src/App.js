import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Box, AppBar, Toolbar, IconButton, Typography, Drawer, List, ListItem, ListItemIcon, ListItemText, Button, Divider } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import LeaderboardIcon from '@mui/icons-material/Leaderboard';
import SportsFootballIcon from '@mui/icons-material/SportsFootball';
import BarChartIcon from '@mui/icons-material/BarChart';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import RefreshIcon from '@mui/icons-material/Refresh';

// Import components
import Login from './components/Login';
import Leaderboard from './components/Leaderboard';
import WeeklyPicks from './components/WeeklyPicks';
import Statistics from './components/Statistics';
import Settings from './components/Settings';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const menuItems = [
  { text: 'Leaderboard', icon: <LeaderboardIcon />, path: '/' },
  { text: 'Weekly Picks', icon: <SportsFootballIcon />, path: '/picks' },
  { text: 'Statistics', icon: <BarChartIcon />, path: '/stats' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  return isAuthenticated ? (
    children
  ) : (
    <Navigate to="/login" state={{ from: location }} replace />
  );
}

function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  if (!isAuthenticated) {
    return <Login />;
  }

  const handleNavigation = (path) => {
    navigate(path);
    toggleDrawer();
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        logout();
        navigate('/login');
      }
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  const handleManualUpdate = async () => {
    try {
      const response = await fetch('/api/admin/update-games', {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        alert(data.message);
      } else {
        const error = await response.json();
        alert(error.error);
      }
    } catch (error) {
      console.error('Error updating games:', error);
      alert('Error updating games');
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            NFL Pick'em
          </Typography>
          <Button color="inherit" onClick={handleLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer}
      >
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
          {user?.is_admin && (
            <>
              <Divider />
              <ListItem button onClick={handleManualUpdate}>
                <ListItemIcon><RefreshIcon /></ListItemIcon>
                <ListItemText primary="Update Games" />
              </ListItem>
            </>
          )}
          <Divider />
          <ListItem button onClick={handleLogout}>
            <ListItemIcon><LogoutIcon /></ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItem>
        </List>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: '100%',
          mt: 8,
        }}
      >
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Leaderboard /></PrivateRoute>} />
          <Route path="/picks" element={<PrivateRoute><WeeklyPicks /></PrivateRoute>} />
          <Route path="/stats" element={<PrivateRoute><Statistics /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
        </Routes>
      </Box>
    </Box>
  );
}

function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithAuth;
