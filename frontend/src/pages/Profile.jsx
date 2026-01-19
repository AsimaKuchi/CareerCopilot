import { useState, useEffect } from "react";
import { API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import {
  User,
  FileText,
  Upload,
  X,
  Plus,
  MapPin,
  DollarSign,
  Briefcase,
  Save,
  CheckCircle,
  Shield,
  Building2,
  TrendingUp,
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

export default function Profile({ user }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  const [newSkill, setNewSkill] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newLocation, setNewLocation] = useState("");
  const [newIndustry, setNewIndustry] = useState("");

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${API}/profile`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch profile");
      const data = await response.json();
      setProfile(data);
    } catch (error) {
      toast.error("Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (updates) => {
    setSaving(true);
    try {
      const response = await fetch(`${API}/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error("Failed to update profile");
      const data = await response.json();
      setProfile(data);
      toast.success("Profile updated successfully");
    } catch (error) {
      toast.error("Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleResumeUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 5MB");
      e.target.value = "";
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API}/profile/resume`, formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setProfile(prev => ({ ...prev, resume_filename: response.data.filename, resume_text: "uploaded" }));
      toast.success("Resume uploaded successfully!");
    } catch (error) {
      console.error("Resume upload error:", error);
      const message = error.response?.data?.detail || error.message || "Failed to upload resume";
      toast.error(message);
    } finally {
      setUploading(false);
      if (e.target) e.target.value = "";
    }
  };

  const addSkill = () => {
    if (!newSkill.trim()) return;
    const skills = [...(profile?.skills || []), newSkill.trim()];
    updateProfile({ skills });
    setNewSkill("");
  };

  const removeSkill = (index) => {
    const skills = (profile?.skills || []).filter((_, i) => i !== index);
    updateProfile({ skills });
  };

  const addTitle = () => {
    if (!newTitle.trim()) return;
    const job_titles = [...(profile?.job_titles || []), newTitle.trim()];
    updateProfile({ job_titles });
    setNewTitle("");
  };

  const removeTitle = (index) => {
    const job_titles = (profile?.job_titles || []).filter((_, i) => i !== index);
    updateProfile({ job_titles });
  };

  const addLocation = () => {
    if (!newLocation.trim()) return;
    const preferred_locations = [...(profile?.preferred_locations || []), newLocation.trim()];
    updateProfile({ preferred_locations });
    setNewLocation("");
  };

  const removeLocation = (index) => {
    const preferred_locations = (profile?.preferred_locations || []).filter((_, i) => i !== index);
    updateProfile({ preferred_locations });
  };

  const handleJobTypeToggle = (type) => {
    const current = profile?.job_type || [];
    const updated = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    updateProfile({ job_type: updated });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} />
        <main className="max-w-4xl mx-auto px-6 py-8">
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="glass-light animate-pulse">
                <CardContent className="p-6">
                  <div className="h-32 bg-white/5 rounded-lg" />
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    );
  }

  const jobTypes = ["full-time", "part-time", "contract", "remote", "internship"];

  return (
    <div className="min-h-screen bg-background" data-testid="profile-page">
      <Navbar user={user} />
      
      <div className="hero-glow opacity-30" />

      <main className="relative z-10 max-w-4xl mx-auto px-6 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">Your Profile</h1>
          <p className="text-muted-foreground">
            Keep your profile updated for better job matches
          </p>
        </div>

        <div className="space-y-6">
          {/* User Info Card */}
          <Card className="glass-light animate-fade-in" data-testid="user-info-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5 text-indigo-400" />
                Account Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold">
                  {user?.name?.charAt(0) || "U"}
                </div>
                <div>
                  <p className="text-lg font-semibold text-foreground">{user?.name}</p>
                  <p className="text-muted-foreground">{user?.email}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Resume Upload Card */}
          <Card className="glass-light animate-fade-in-delay-1" data-testid="resume-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-400" />
                Resume
              </CardTitle>
            </CardHeader>
            <CardContent>
              {profile?.resume_filename ? (
                <div className="flex items-center justify-between p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    <div>
                      <p className="font-medium text-foreground">{profile.resume_filename}</p>
                      <p className="text-sm text-muted-foreground">Resume uploaded</p>
                    </div>
                  </div>
                  <div>
                    <input
                      type="file"
                      id="resume-replace-input"
                      accept=".pdf,.doc,.docx,.txt"
                      onChange={handleResumeUpload}
                      className="hidden"
                    />
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="border-white/10" 
                      disabled={uploading}
                      onClick={() => document.getElementById('resume-replace-input').click()}
                    >
                      {uploading ? "Uploading..." : "Replace"}
                    </Button>
                  </div>
                </div>
              ) : (
                <label className="cursor-pointer">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleResumeUpload}
                    className="hidden"
                    data-testid="resume-upload-input"
                  />
                  <div className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-indigo-500/50 transition-colors">
                    <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-foreground font-medium mb-1">
                      {uploading ? "Uploading..." : "Upload your resume"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      PDF, DOC, DOCX, or TXT (Max 5MB)
                    </p>
                  </div>
                </label>
              )}
            </CardContent>
          </Card>

          {/* Skills Card */}
          <Card className="glass-light animate-fade-in-delay-2" data-testid="skills-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-amber-400" />
                Skills
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {profile?.skills?.map((skill, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="bg-white/5 hover:bg-white/10 px-3 py-1 cursor-pointer group"
                    onClick={() => removeSkill(i)}
                  >
                    {skill}
                    <X className="w-3 h-3 ml-2 opacity-50 group-hover:opacity-100" />
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  data-testid="skill-input"
                  placeholder="Add a skill (e.g., JavaScript, Project Management)"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addSkill()}
                  className="bg-white/5 border-white/10"
                />
                <Button
                  data-testid="add-skill-btn"
                  onClick={addSkill}
                  className="bg-indigo-500 hover:bg-indigo-600"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Job Titles Card */}
          <Card className="glass-light" data-testid="job-titles-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-rose-400" />
                Desired Job Titles
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {profile?.job_titles?.map((title, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="bg-white/5 hover:bg-white/10 px-3 py-1 cursor-pointer group"
                    onClick={() => removeTitle(i)}
                  >
                    {title}
                    <X className="w-3 h-3 ml-2 opacity-50 group-hover:opacity-100" />
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  data-testid="job-title-input"
                  placeholder="Add a job title (e.g., Software Engineer)"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addTitle()}
                  className="bg-white/5 border-white/10"
                />
                <Button
                  data-testid="add-title-btn"
                  onClick={addTitle}
                  className="bg-indigo-500 hover:bg-indigo-600"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Locations Card */}
          <Card className="glass-light" data-testid="locations-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-indigo-400" />
                Preferred Locations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {profile?.preferred_locations?.map((loc, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="bg-white/5 hover:bg-white/10 px-3 py-1 cursor-pointer group"
                    onClick={() => removeLocation(i)}
                  >
                    {loc}
                    <X className="w-3 h-3 ml-2 opacity-50 group-hover:opacity-100" />
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  data-testid="location-input"
                  placeholder="Add a location (e.g., New York, Remote)"
                  value={newLocation}
                  onChange={(e) => setNewLocation(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addLocation()}
                  className="bg-white/5 border-white/10"
                />
                <Button
                  data-testid="add-location-btn"
                  onClick={addLocation}
                  className="bg-indigo-500 hover:bg-indigo-600"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Experience & Salary Card */}
          <Card className="glass-light" data-testid="experience-salary-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-emerald-400" />
                Experience & Salary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="text-foreground mb-2 block">Years of Experience</Label>
                <Input
                  data-testid="experience-input"
                  type="number"
                  min="0"
                  value={profile?.experience_years || 0}
                  onChange={(e) => updateProfile({ experience_years: parseInt(e.target.value) || 0 })}
                  className="bg-white/5 border-white/10 w-32"
                />
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-foreground mb-2 block">Minimum Salary ($)</Label>
                  <Input
                    data-testid="salary-min-input"
                    type="number"
                    placeholder="e.g., 50000"
                    value={profile?.salary_min || ""}
                    onChange={(e) => updateProfile({ salary_min: parseInt(e.target.value) || null })}
                    className="bg-white/5 border-white/10"
                  />
                </div>
                <div>
                  <Label className="text-foreground mb-2 block">Maximum Salary ($)</Label>
                  <Input
                    data-testid="salary-max-input"
                    type="number"
                    placeholder="e.g., 100000"
                    value={profile?.salary_max || ""}
                    onChange={(e) => updateProfile({ salary_max: parseInt(e.target.value) || null })}
                    className="bg-white/5 border-white/10"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Job Type Card */}
          <Card className="glass-light" data-testid="job-type-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-indigo-400" />
                Job Type Preferences
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {jobTypes.map((type) => (
                  <button
                    key={type}
                    data-testid={`job-type-${type}`}
                    onClick={() => handleJobTypeToggle(type)}
                    className={`px-4 py-2 rounded-lg capitalize transition-all ${
                      profile?.job_type?.includes(type)
                        ? "bg-indigo-500 text-white"
                        : "bg-white/5 text-muted-foreground hover:bg-white/10"
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
