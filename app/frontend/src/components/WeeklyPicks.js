import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Paper,
  Divider
} from '@mui/material';
import { ArrowBack, ArrowForward } from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

export default function WeeklyPicks() {
  const [currentWeek, setCurrentWeek] = useState(1);
  const [games, setGames] = useState([]);
  const [picks, setPicks] = useState({});
  const [mnfPoints, setMnfPoints] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLocked, setIsLocked] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchWeekData();
  }, [currentWeek]);

  const fetchWeekData = async () => {
    try {
      setLoading(true);
      const [gamesResponse, picksResponse] = await Promise.all([
        axios.get(`/api/games?week=${currentWeek}`),
        axios.get(`/api/picks?week=${currentWeek}`)
      ]);

      setGames(gamesResponse.data.games);
      
      // Convert picks array to object for easier handling
      const picksObj = {};
      picksResponse.data.picks.forEach(pick => {
        picksObj[pick.game_id] = pick.picked_team;
        if (pick.mnf_total_points) {
          setMnfPoints(pick.mnf_total_points.toString());
        }
      });
      setPicks(picksObj);

      // Check if picks are locked
      const now = new Date();
      const firstGame = gamesResponse.data.games[0];
      if (firstGame) {
        const gameStart = new Date(firstGame.start_time);
        const lockTime = new Date(gameStart.getTime() - (2 * 60 * 60 * 1000)); // 2 hours before
        setIsLocked(now >= lockTime && !user.is_admin);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching week data:', error);
      setError('Failed to load games and picks');
      setLoading(false);
    }
  };

  const handlePickChange = (gameId, team) => {
    setPicks(prev => ({
      ...prev,
      [gameId]: team
    }));
  };

  const handleSubmit = async () => {
    try {
      setError('');
      setSuccess('');

      // Validate all games have picks
      const unpickedGames = games.filter(game => !picks[game.id]);
      if (unpickedGames.length > 0) {
        setError('Please make picks for all games');
        return;
      }

      // Validate MNF points for games on Monday
      const mnfGames = games.filter(game => game.is_mnf);
      if (mnfGames.length > 0 && (!mnfPoints || isNaN(mnfPoints))) {
        setError('Please enter a valid prediction for Monday Night Football total points');
        return;
      }

      const response = await axios.post('/api/picks', {
        week: currentWeek,
        picks: Object.entries(picks).map(([game_id, team]) => ({
          game_id: parseInt(game_id),
          team
        })),
        mnf_total_points: parseInt(mnfPoints)
      });

      setSuccess('Picks saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error.response?.data?.message || 'Failed to save picks');
    }
  };

  const navigateWeek = (direction) => {
    setCurrentWeek(prev => prev + direction);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton
          onClick={() => navigateWeek(-1)}
          disabled={currentWeek === 1}
        >
          <ArrowBack />
        </IconButton>
        <Typography variant="h6" sx={{ mx: 2 }}>
          Week {currentWeek}
        </Typography>
        <IconButton
          onClick={() => navigateWeek(1)}
          disabled={currentWeek === 18}
        >
          <ArrowForward />
        </IconButton>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      {isLocked && !user.is_admin && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Picks are locked for this week
        </Alert>
      )}

      <Grid container spacing={2}>
        {games.map((game) => (
          <Grid item xs={12} key={game.id}>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Grid container alignItems="center" spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="textSecondary">
                    {new Date(game.start_time).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={8}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Button
                      variant={picks[game.id] === game.away_team ? "contained" : "outlined"}
                      onClick={() => handlePickChange(game.id, game.away_team)}
                      disabled={isLocked && !user.is_admin}
                      sx={{ flex: 1, mr: 1 }}
                    >
                      {game.away_team}
                    </Button>
                    <Typography variant="body2" sx={{ mx: 2 }}>@</Typography>
                    <Button
                      variant={picks[game.id] === game.home_team ? "contained" : "outlined"}
                      onClick={() => handlePickChange(game.id, game.home_team)}
                      disabled={isLocked && !user.is_admin}
                      sx={{ flex: 1, ml: 1 }}
                    >
                      {game.home_team}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {games.some(game => game.is_mnf) && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Monday Night Football Total Points
            </Typography>
            <TextField
              type="number"
              label="Predicted Total Points"
              value={mnfPoints}
              onChange={(e) => setMnfPoints(e.target.value)}
              disabled={isLocked && !user.is_admin}
              fullWidth
              helperText="Enter your prediction for the total points scored in all Monday night games"
            />
          </CardContent>
        </Card>
      )}

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={isLocked && !user.is_admin}
        >
          Save Picks
        </Button>
      </Box>
    </Box>
  );
}
