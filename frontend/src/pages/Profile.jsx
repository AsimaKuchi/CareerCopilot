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
  Phone,
  Linkedin,
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

  const addIndustry = () => {
    if (!newIndustry.trim()) return;
    const industries = profile?.industries || [];
    if (industries.length >= 3) {
      toast.error("Maximum 3 industries allowed. Remove one to add another.");
      return;
    }
    updateProfile({ industries: [...industries, newIndustry.trim()] });
    setNewIndustry("");
  };

  const removeIndustry = (index) => {
    const industries = (profile?.industries || []).filter((_, i) => i !== index);
    updateProfile({ industries });
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
                  placeholder="Add a location (e.g., Toronto, Ontario)"
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
              
              {/* Preferred Work Arrangement */}
              <div className="pt-4 border-t border-white/10">
                <Label className="text-foreground mb-2 block">Preferred Work Arrangement</Label>
                <Select
                  value={profile?.work_arrangement || ""}
                  onValueChange={(value) => updateProfile({ work_arrangement: value })}
                >
                  <SelectTrigger className="bg-white/5 border-white/10" data-testid="work-arrangement-select">
                    <SelectValue placeholder="Select your preference" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="remote">Remote</SelectItem>
                    <SelectItem value="hybrid">Hybrid</SelectItem>
                    <SelectItem value="onsite">On-site</SelectItem>
                    <SelectItem value="flexible">Flexible</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground mt-2">
                  This helps us prioritize jobs that match your work style preferences
                </p>
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
              <div>
                <Label className="text-foreground mb-2 block">Salary Expectations ($)</Label>
                <Input
                  data-testid="salary-expectations-input"
                  type="number"
                  placeholder="e.g., 75000"
                  value={profile?.salary_min || ""}
                  onChange={(e) => updateProfile({ salary_min: parseInt(e.target.value) || null })}
                  className="bg-white/5 border-white/10"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Your desired annual salary
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Contact Information Card */}
          <Card className="glass-light" data-testid="contact-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-emerald-400" />
                Contact Information (For Auto-Fill)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-foreground mb-2 block">
                  Phone Number
                  <span className="text-red-400 ml-1">*</span>
                </Label>
                <Input
                  data-testid="phone-input"
                  type="tel"
                  placeholder="e.g., +1 (555) 123-4567"
                  value={profile?.phone_number || ""}
                  onChange={(e) => updateProfile({ phone_number: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
                <p className="text-sm text-gray-400 mt-1">
                  Required for most job applications. Used to auto-fill application forms.
                </p>
              </div>
              <div>
                <Label className="text-foreground mb-2 flex items-center gap-2">
                  <Linkedin className="w-4 h-4 text-blue-400" />
                  LinkedIn Profile URL
                  <span className="text-gray-400 text-xs font-normal">(Optional)</span>
                </Label>
                <Input
                  data-testid="linkedin-input"
                  type="url"
                  placeholder="e.g., https://linkedin.com/in/yourprofile"
                  value={profile?.linkedin_url || ""}
                  onChange={(e) => updateProfile({ linkedin_url: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
                <p className="text-sm text-gray-400 mt-1">
                  Optional but recommended. Many employers request your LinkedIn profile.
                </p>
              </div>

              <div>
                <Label className="text-foreground mb-2 block">GitHub URL (for tech roles)</Label>
                <Input
                  data-testid="github-input"
                  type="url"
                  placeholder="e.g., https://github.com/yourusername"
                  value={profile?.github_url || ""}
                  onChange={(e) => updateProfile({ github_url: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
              </div>

              <div>
                <Label className="text-foreground mb-2 block">Portfolio / Personal Website</Label>
                <Input
                  data-testid="portfolio-input"
                  type="url"
                  placeholder="e.g., https://yourportfolio.com"
                  value={profile?.portfolio_url || ""}
                  onChange={(e) => updateProfile({ portfolio_url: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
              </div>
            </CardContent>
          </Card>

          {/* Auto-Application Details Card */}
          <Card className="glass-light" data-testid="auto-application-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-purple-400" />
                Auto-Application Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-sm text-muted-foreground">
                These fields are used to automatically fill out job application forms. Complete them once, apply everywhere.
              </p>

              <div>
                <Label className="text-foreground mb-2 block">Current Company</Label>
                <Input
                  data-testid="current-company-input"
                  placeholder="e.g., Acme Corp (leave blank if unemployed)"
                  value={profile?.current_company || ""}
                  onChange={(e) => updateProfile({ current_company: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
              </div>

              <div>
                <Label className="text-foreground mb-2 block">
                  Willing to Relocate?
                  <span className="text-red-400 ml-1">*</span>
                </Label>
                <Select
                  value={profile?.willing_to_relocate || ""}
                  onValueChange={(value) => updateProfile({ willing_to_relocate: value })}
                >
                  <SelectTrigger className="bg-white/5 border-white/10" data-testid="relocation-select">
                    <SelectValue placeholder="Select your preference" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="yes">Yes - willing to relocate</SelectItem>
                    <SelectItem value="no">No - not willing to relocate</SelectItem>
                    <SelectItem value="open_to_discussion">Open to discussion</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-foreground mb-2 block">
                  Notice Period / When can you start?
                  <span className="text-red-400 ml-1">*</span>
                </Label>
                <Select
                  value={profile?.notice_period || ""}
                  onValueChange={(value) => updateProfile({ notice_period: value })}
                >
                  <SelectTrigger className="bg-white/5 border-white/10" data-testid="notice-period-select">
                    <SelectValue placeholder="Select your availability" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="immediately">Immediately available</SelectItem>
                    <SelectItem value="two_weeks">2 weeks notice</SelectItem>
                    <SelectItem value="one_month">1 month notice</SelectItem>
                    <SelectItem value="two_months">2 months notice</SelectItem>
                    <SelectItem value="three_months_plus">3+ months notice</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-foreground mb-2 block">
                  Default answer for &quot;How did you hear about us?&quot;
                </Label>
                <Input
                  data-testid="referral-source-input"
                  placeholder="e.g., LinkedIn, Company website, Referral"
                  value={profile?.referral_source || ""}
                  onChange={(e) => updateProfile({ referral_source: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
                <p className="text-sm text-gray-400 mt-1">
                  This will be used as the default answer when applications ask this question
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Address Card */}
          <Card className="glass-light" data-testid="address-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-rose-400" />
                Full Address (for applications)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Some job applications require your full address. This will be auto-filled when needed.
              </p>

              <div>
                <Label className="text-foreground mb-2 block">Street Address</Label>
                <Input
                  data-testid="address-street-input"
                  placeholder="e.g., 123 Main Street, Apt 4B"
                  value={profile?.address_street || ""}
                  onChange={(e) => updateProfile({ address_street: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-foreground mb-2 block">City</Label>
                  <Input
                    data-testid="address-city-input"
                    placeholder="e.g., Toronto"
                    value={profile?.address_city || ""}
                    onChange={(e) => updateProfile({ address_city: e.target.value })}
                    className="bg-white/5 border-white/10"
                  />
                </div>
                <div>
                  <Label className="text-foreground mb-2 block">State/Province</Label>
                  <Input
                    data-testid="address-state-input"
                    placeholder="e.g., Ontario"
                    value={profile?.address_state || ""}
                    onChange={(e) => updateProfile({ address_state: e.target.value })}
                    className="bg-white/5 border-white/10"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-foreground mb-2 block">Postal/ZIP Code</Label>
                  <Input
                    data-testid="address-postal-input"
                    placeholder="e.g., M5V 1A1"
                    value={profile?.address_postal_code || ""}
                    onChange={(e) => updateProfile({ address_postal_code: e.target.value })}
                    className="bg-white/5 border-white/10"
                  />
                </div>
                <div>
                  <Label className="text-foreground mb-2 block">Country</Label>
                  <Input
                    data-testid="address-country-input"
                    placeholder="e.g., Canada"
                    value={profile?.address_country || ""}
                    onChange={(e) => updateProfile({ address_country: e.target.value })}
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

          {/* Work Authorization Card */}
          <Card className="glass-light" data-testid="work-authorization-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-cyan-400" />
                Work Authorization (Canada)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                This helps us filter out jobs that require specific work authorization you may not have.
              </p>
              <Select
                value={profile?.work_authorization || ""}
                onValueChange={(value) => updateProfile({ work_authorization: value })}
              >
                <SelectTrigger className="bg-white/5 border-white/10 w-full md:w-80" data-testid="work-authorization-select">
                  <SelectValue placeholder="Select your work authorization status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="canadian_citizen">Canadian Citizen</SelectItem>
                  <SelectItem value="permanent_resident">Permanent Resident (PR)</SelectItem>
                  <SelectItem value="work_permit">Work Permit (PGWP, LMIA, etc.)</SelectItem>
                  <SelectItem value="require_sponsorship">Require Employer Sponsorship</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Industries Card */}
          <Card className="glass-light" data-testid="industries-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-orange-400" />
                Target Industries (Max 3)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 mb-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile?.open_to_any_industry || false}
                    onChange={(e) => updateProfile({ open_to_any_industry: e.target.checked })}
                    className="w-4 h-4 rounded border-white/20 bg-white/5 text-indigo-500 focus:ring-indigo-500"
                    data-testid="open-to-any-industry-checkbox"
                  />
                  <span className="text-sm text-foreground">Open to any industry</span>
                </label>
              </div>
              {!profile?.open_to_any_industry && (
                <>
                  <div className="flex flex-wrap gap-2">
                    {profile?.industries?.map((industry, i) => (
                      <Badge
                        key={i}
                        variant="secondary"
                        className="bg-white/5 hover:bg-white/10 px-3 py-1 cursor-pointer group"
                        onClick={() => removeIndustry(i)}
                      >
                        {industry}
                        <X className="w-3 h-3 ml-2 opacity-50 group-hover:opacity-100" />
                      </Badge>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Select
                      value={newIndustry}
                      onValueChange={setNewIndustry}
                    >
                      <SelectTrigger className="bg-white/5 border-white/10 flex-1" data-testid="industry-select">
                        <SelectValue placeholder="Select an industry" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="technology">Technology / Software</SelectItem>
                        <SelectItem value="finance">Finance / Banking</SelectItem>
                        <SelectItem value="healthcare">Healthcare / Medical</SelectItem>
                        <SelectItem value="retail">Retail / E-commerce</SelectItem>
                        <SelectItem value="manufacturing">Manufacturing / Industrial</SelectItem>
                        <SelectItem value="consulting">Consulting / Professional Services</SelectItem>
                        <SelectItem value="media">Media / Entertainment</SelectItem>
                        <SelectItem value="education">Education</SelectItem>
                        <SelectItem value="government">Government / Public Sector</SelectItem>
                        <SelectItem value="nonprofit">Non-profit</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      data-testid="add-industry-btn"
                      onClick={addIndustry}
                      disabled={(profile?.industries?.length || 0) >= 3}
                      className="bg-indigo-500 hover:bg-indigo-600"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {3 - (profile?.industries?.length || 0)} slots remaining
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {/* Seniority Level Card */}
          <Card className="glass-light" data-testid="seniority-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-violet-400" />
                Target Seniority Level
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                We&apos;ll prioritize roles that match your career level.
              </p>
              <Select
                value={profile?.seniority_level || ""}
                onValueChange={(value) => updateProfile({ seniority_level: value })}
              >
                <SelectTrigger className="bg-white/5 border-white/10 w-full md:w-80" data-testid="seniority-select">
                  <SelectValue placeholder="Select your target seniority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="entry">Entry Level / Intern</SelectItem>
                  <SelectItem value="junior">Junior (0-2 years)</SelectItem>
                  <SelectItem value="mid">Mid-Level (2-5 years)</SelectItem>
                  <SelectItem value="senior">Senior (5-8 years)</SelectItem>
                  <SelectItem value="lead">Lead / Staff (8+ years)</SelectItem>
                  <SelectItem value="manager">Manager</SelectItem>
                  <SelectItem value="director">Director / VP</SelectItem>
                  <SelectItem value="executive">Executive (C-Level)</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
