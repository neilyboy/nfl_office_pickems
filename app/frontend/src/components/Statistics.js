import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider
} from '@mui/material';
import axios from 'axios';

export default function Statistics() {
  const [selectedUser, setSelectedUser] = useState('');
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      fetchUserStats();
    }
  }, [selectedUser]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/api/users');
      setUsers(response.data);
      if (response.data.length > 0) {
        setSelectedUser(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchUserStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/stats?user_id=${selectedUser}`);
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching user stats:', error);
      setLoading(false);
    }
  };

  if (!stats && loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel>Select Player</InputLabel>
        <Select
          value={selectedUser}
          label="Select Player"
          onChange={(e) => setSelectedUser(e.target.value)}
        >
          {users.map((user) => (
            <MenuItem key={user.id} value={user.id}>
              {user.username}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {stats && (
        <Grid container spacing={3}>
          {/* Performance Overview Card */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Overview
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {(stats.totalAccuracy * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Total Accuracy ({stats.totalCorrect}/{stats.totalPicks})
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        Week {stats.bestWeek.week}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Best Week ({stats.bestWeek.correct} correct)
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {stats.averagePerWeek.toFixed(1)}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Average Correct Per Week
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Weekly Performance Card */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Weekly Performance
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Week</TableCell>
                        <TableCell align="center">Correct</TableCell>
                        <TableCell align="center">Total</TableCell>
                        <TableCell align="center">Accuracy</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.weeklyPerformance.map((week) => (
                        <TableRow key={week.week}>
                          <TableCell>Week {week.week}</TableCell>
                          <TableCell align="center">{week.correct}</TableCell>
                          <TableCell align="center">{week.total}</TableCell>
                          <TableCell align="center">
                            {((week.correct / week.total) * 100).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Team Performance Card */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Team Performance
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Team</TableCell>
                        <TableCell align="center">Picks</TableCell>
                        <TableCell align="center">Wins</TableCell>
                        <TableCell align="center">Accuracy</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.teamPerformance.map((team) => (
                        <TableRow key={team.team}>
                          <TableCell>{team.team}</TableCell>
                          <TableCell align="center">{team.picks}</TableCell>
                          <TableCell align="center">{team.wins}</TableCell>
                          <TableCell align="center">
                            {((team.wins / team.picks) * 100).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
