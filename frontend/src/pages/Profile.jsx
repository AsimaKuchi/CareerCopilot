import React, { useState, useEffect, useRef } from "react";
import { API } from "@/App";
import { apiFetch } from "@/utils/apiFetch";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import SessionManagement from "@/components/SessionManagement";
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
  Clock,
  Pencil,
  Mail,
  GraduationCap,
  Sparkles,
  Loader2,
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { toast } from "sonner";
import SkillsCombobox from "@/components/SkillsCombobox";

export default function Profile({ user }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [pendingChanges, setPendingChanges] = useState({});
  const debounceTimerRef = useRef(null);
  
  const [newSkill, setNewSkill] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newLocation, setNewLocation] = useState("");
  const [newIndustry, setNewIndustry] = useState("");
  const [editingSkillIndex, setEditingSkillIndex] = useState(null);
  const [prefillSuggestions, setPrefillSuggestions] = useState(null);
  const [prefillLoading, setPrefillLoading] = useState(false);

  const yearsOptions = [
    { value: "<1", label: "<1 year" },
    { value: "1–2", label: "1–2 years" },
    { value: "3–5", label: "3–5 years" },
    { value: "5+", label: "5+ years" },
  ];

  useEffect(() => {
    fetchProfile();
  }, []);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await apiFetch(`${API}/profile`, {
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

  // Immediate save for dropdowns/toggles (no debounce needed)
  const updateProfileImmediate = async (updates) => {
    setSaving(true);
    try {
      const response = await apiFetch(`${API}/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error("Failed to update profile");
      const data = await response.json();
      setProfile(data);
      toast.success("Profile updated");
    } catch (error) {
      toast.error("Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  // Debounced save for text inputs (waits 1 second after user stops typing)
  const updateProfileDebounced = (updates) => {
    // Update local state immediately for responsive UI
    setProfile(prev => ({ ...prev, ...updates }));
    setPendingChanges(prev => ({ ...prev, ...updates }));
    
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Set new timer to save after 1 second of no typing
    debounceTimerRef.current = setTimeout(async () => {
      const allPendingChanges = { ...pendingChanges, ...updates };
      if (Object.keys(allPendingChanges).length === 0) return;
      
      setSaving(true);
      try {
        const response = await apiFetch(`${API}/profile`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(allPendingChanges),
        });
        if (!response.ok) throw new Error("Failed to update profile");
        const data = await response.json();
        setProfile(data);
        setPendingChanges({});
        toast.success("Profile updated");
      } catch (error) {
        toast.error("Failed to update profile");
      } finally {
        setSaving(false);
      }
    }, 1000);
  };

  // Wrapper that decides which update method to use
  const updateProfile = (updates, immediate = false) => {
    if (immediate) {
      updateProfileImmediate(updates);
    } else {
      updateProfileDebounced(updates);
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
      // Trigger field extraction for pre-fill
      extractFieldsFromResume();
    } catch (error) {
      console.error("Resume upload error:", error);
      const message = error.response?.data?.detail || error.message || "Failed to upload resume";
      toast.error(message);
    } finally {
      setUploading(false);
      if (e.target) e.target.value = "";
    }
  };

  const extractFieldsFromResume = async () => {
    setPrefillLoading(true);
    try {
      const res = await apiFetch(`${API}/profile/resume/extract-fields`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        if (data.has_suggestions) {
          setPrefillSuggestions(data.suggestions);
        }
      }
    } catch {
      /* silent */
    } finally {
      setPrefillLoading(false);
    }
  };

  const applyPrefill = async () => {
    if (!prefillSuggestions) return;
    const updates = {};
    const s = prefillSuggestions;

    if (s.phone_number) updates.phone_number = s.phone_number;
    if (s.highest_education) updates.highest_education = s.highest_education;
    if (s.address_city) updates.address_city = s.address_city;
    if (s.address_state) updates.address_state = s.address_state;
    if (s.address_country) updates.address_country = s.address_country;
    if (s.experience_years) updates.experience_years = s.experience_years;
    if (s.first_name) updates.first_name = s.first_name;
    if (s.last_name) updates.last_name = s.last_name;

    if (s.skills) {
      updates.skills = s.skills.map(name => ({ name, years: null }));
    } else if (s.new_skills) {
      const existing = profile?.skills || [];
      const added = s.new_skills.map(name => ({ name, years: null }));
      updates.skills = [...existing, ...added];
    }

    if (s.job_titles) updates.job_titles = s.job_titles;

    await updateProfile(updates);
    setPrefillSuggestions(null);
    toast.success("Profile updated with resume data!");
    fetchProfile();
  };



  const addSkill = () => {
    if (!newSkill.trim()) return;
    // Add skill as object with name and optional years
    const newSkillObj = { name: newSkill.trim(), years: null };
    const skills = [...(profile?.skills || []), newSkillObj];
    updateProfile({ skills });
    setNewSkill("");
  };

  const removeSkill = (index) => {
    const skills = (profile?.skills || []).filter((_, i) => i !== index);
    updateProfile({ skills });
  };

  const updateSkillYears = (index, years) => {
    const skills = [...(profile?.skills || [])];
    if (skills[index]) {
      skills[index] = { ...skills[index], years: years || null };
      updateProfile({ skills });
    }
    setEditingSkillIndex(null);
  };

  const getSkillName = (skill) => {
    // Handle both old string format and new object format
    if (typeof skill === "string") return skill;
    return skill?.name || "";
  };

  const getSkillYears = (skill) => {
    if (typeof skill === "string") return null;
    return skill?.years || null;
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

          {/* Pre-fill from Resume Banner */}
          {prefillLoading && (
            <Card className="border-indigo-200 bg-indigo-50/50 animate-fade-in">
              <CardContent className="py-4 flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-indigo-500 animate-spin shrink-0" />
                <p className="text-sm text-indigo-700">Analyzing your resume for profile data...</p>
              </CardContent>
            </Card>
          )}

          {prefillSuggestions && !prefillLoading && (
            <Card className="border-indigo-200 bg-indigo-50/50 animate-fade-in" data-testid="prefill-banner">
              <CardContent className="py-4 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" />
                    <div>
                      <p className="font-medium text-sm text-indigo-800">We found profile data in your resume</p>
                      <p className="text-xs text-indigo-600 mt-0.5">Only empty fields will be filled — your existing data won't be changed.</p>
                    </div>
                  </div>
                  <button onClick={() => setPrefillSuggestions(null)} className="text-indigo-400 hover:text-indigo-600 p-1">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  {prefillSuggestions.phone_number && <Badge variant="outline" className="bg-white">Phone: {prefillSuggestions.phone_number}</Badge>}
                  {prefillSuggestions.highest_education && <Badge variant="outline" className="bg-white">Education: {prefillSuggestions.highest_education}</Badge>}
                  {prefillSuggestions.skills && <Badge variant="outline" className="bg-white">{prefillSuggestions.skills.length} skills</Badge>}
                  {prefillSuggestions.new_skills && <Badge variant="outline" className="bg-white">{prefillSuggestions.new_skills.length} new skills</Badge>}
                  {prefillSuggestions.job_titles && <Badge variant="outline" className="bg-white">Job titles: {prefillSuggestions.job_titles.join(", ")}</Badge>}
                  {prefillSuggestions.address_city && <Badge variant="outline" className="bg-white">Location: {prefillSuggestions.address_city}</Badge>}
                  {prefillSuggestions.experience_years && <Badge variant="outline" className="bg-white">{prefillSuggestions.experience_years} yrs experience</Badge>}
                  {prefillSuggestions.first_name && <Badge variant="outline" className="bg-white">Name: {prefillSuggestions.first_name} {prefillSuggestions.last_name || ""}</Badge>}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={applyPrefill} data-testid="apply-prefill-btn">
                    <Sparkles className="w-3.5 h-3.5 mr-1.5" />Pre-fill Profile
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setPrefillSuggestions(null)}>
                    Dismiss
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Skills Card */}
          <Card className="glass-light animate-fade-in-delay-2" data-testid="skills-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-amber-400" />
                Skills
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                Click a skill to add years of experience (optional)
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {profile?.skills?.map((skill, i) => (
                  <Popover 
                    key={i} 
                    open={editingSkillIndex === i}
                    onOpenChange={(open) => setEditingSkillIndex(open ? i : null)}
                  >
                    <PopoverTrigger asChild>
                      <Badge
                        variant="secondary"
                        className={`px-3 py-1.5 cursor-pointer group transition-all ${
                          getSkillYears(skill) 
                            ? "bg-amber-500/20 border border-amber-500/30 hover:bg-amber-500/30" 
                            : "bg-white/5 hover:bg-white/10"
                        }`}
                      >
                        <span className="flex items-center gap-1.5">
                          {getSkillName(skill)}
                          {getSkillYears(skill) && (
                            <span className="text-amber-400 text-xs font-normal">
                              · {getSkillYears(skill)} yrs
                            </span>
                          )}
                          {!getSkillYears(skill) && (
                            <Pencil className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-50" />
                          )}
                        </span>
                      </Badge>
                    </PopoverTrigger>
                    <PopoverContent className="w-56 p-3" align="start">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{getSkillName(skill)}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                            onClick={() => {
                              removeSkill(i);
                              setEditingSkillIndex(null);
                            }}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Years of experience (optional)
                          </Label>
                          <Select
                            value={getSkillYears(skill) || "none"}
                            onValueChange={(value) => updateSkillYears(i, value === "none" ? null : value)}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue placeholder="Select years" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">Not specified</SelectItem>
                              {yearsOptions.map((opt) => (
                                <SelectItem key={opt.value} value={opt.value}>
                                  {opt.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </PopoverContent>
                  </Popover>
                ))}
              </div>
              <SkillsCombobox
                selectedSkills={profile?.skills || []}
                onAddSkill={(skillName) => {
                  const newSkillObj = { name: skillName, years: null };
                  const skills = [...(profile?.skills || []), newSkillObj];
                  updateProfile({ skills });
                }}
              />
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
                  value={profile?.preferred_work_arrangement || ""}
                  onValueChange={(value) => updateProfile({ preferred_work_arrangement: value }, true)}
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
                <Label className="text-foreground mb-2 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-blue-400" />
                  Email Address
                  <span className="text-red-400 ml-1">*</span>
                </Label>
                <Input
                  data-testid="email-input"
                  type="email"
                  placeholder="e.g., john.doe@email.com"
                  value={profile?.email || ""}
                  onChange={(e) => updateProfile({ email: e.target.value })}
                  className="bg-white/5 border-white/10"
                />
                <p className="text-sm text-gray-400 mt-1">
                  Your preferred contact email for job applications.
                </p>
              </div>
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
                <Label className="text-foreground mb-2 block">
                  GitHub URL
                  <span className="text-gray-400 text-xs font-normal ml-2">(Optional - for tech roles)</span>
                </Label>
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
                <Label className="text-foreground mb-2 block">
                  Portfolio / Personal Website
                  <span className="text-gray-400 text-xs font-normal ml-2">(Optional)</span>
                </Label>
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

          {/* Education Card */}
          <Card className="glass-light" data-testid="education-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-purple-400" />
                Education
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-foreground mb-2 block">
                  Highest Level of Education
                </Label>
                <Select
                  value={profile?.highest_education || ""}
                  onValueChange={(value) => updateProfile({ highest_education: value })}
                >
                  <SelectTrigger data-testid="education-select" className="bg-white/5 border-white/10">
                    <SelectValue placeholder="Select your highest education level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="high_school">High School Diploma / GED</SelectItem>
                    <SelectItem value="some_college">Some College (No Degree)</SelectItem>
                    <SelectItem value="associate">Associate Degree</SelectItem>
                    <SelectItem value="bachelor">Bachelor&apos;s Degree</SelectItem>
                    <SelectItem value="master">Master&apos;s Degree</SelectItem>
                    <SelectItem value="doctorate">Doctorate (PhD, MD, JD, etc.)</SelectItem>
                    <SelectItem value="professional">Professional Certification</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-400 mt-1">
                  Used for job applications that require education information.
                </p>
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
                  onValueChange={(value) => updateProfile({ willing_to_relocate: value }, true)}
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
                  onValueChange={(value) => updateProfile({ notice_period: value }, true)}
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

          {/* Location Card */}
          <Card className="glass-light" data-testid="address-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-rose-400" />
                Location
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Your location helps with job matching and application forms.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
                  <Label className="text-foreground mb-2 block">Province / State</Label>
                  <Input
                    data-testid="address-state-input"
                    placeholder="e.g., Ontario"
                    value={profile?.address_state || ""}
                    onChange={(e) => updateProfile({ address_state: e.target.value })}
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
                onValueChange={(value) => updateProfile({ work_authorization: value }, true)}
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
                    onChange={(e) => updateProfile({ open_to_any_industry: e.target.checked }, true)}
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
                onValueChange={(value) => updateProfile({ seniority_level: value }, true)}
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

        {/* Session Management */}
        <div className="mt-6">
          <SessionManagement />
        </div>
      </main>
    </div>
  );
}
