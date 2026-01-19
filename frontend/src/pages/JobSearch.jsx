import { useState, useEffect } from "react";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import Navbar from "@/components/Navbar";
import {
  Search,
  MapPin,
  Building,
  Clock,
  DollarSign,
  ExternalLink,
  Sparkles,
  FileText,
  MessageSquare,
  Loader2,
  Briefcase,
  Globe,
  Wand2,
} from "lucide-react";
import { toast } from "sonner";

export default function JobSearch({ user }) {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [employmentType, setEmploymentType] = useState("");
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showApplyDialog, setShowApplyDialog] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [generatingResume, setGeneratingResume] = useState(false);
  const [generatingCover, setGeneratingCover] = useState(false);
  const [optimizedResume, setOptimizedResume] = useState("");
  const [coverLetter, setCoverLetter] = useState("");

  // Fetch profile and auto-search on page load
  useEffect(() => {
    fetchProfileAndSearch();
  }, []);

  const fetchProfileAndSearch = async () => {
    try {
      const response = await fetch(`${API}/profile`, {
        credentials: "include",
      });
      if (response.ok) {
        const profileData = await response.json();
        setProfile(profileData);
        
        // Auto-search based on profile if user has job titles or skills
        if (profileData.job_titles?.length > 0 || profileData.skills?.length > 0) {
          const autoQuery = profileData.job_titles?.[0] || profileData.skills?.slice(0, 3).join(" ");
          const autoLocation = profileData.preferred_locations?.[0] || "";
          
          setQuery(autoQuery);
          setLocation(autoLocation);
          
          // Auto search with profile data
          await searchJobsWithParams(autoQuery, autoLocation, "");
        }
      }
    } catch (error) {
      console.error("Failed to fetch profile:", error);
    } finally {
      setInitialLoading(false);
    }
  };

  const searchJobsWithParams = async (searchQuery, searchLocation, searchEmploymentType) => {
    if (!searchQuery?.trim()) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API}/jobs/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          query: searchQuery.trim(),
          location: searchLocation?.trim() || null,
          employment_types: searchEmploymentType || null,
          page: 1,
          num_pages: 1,
        }),
      });

      if (!response.ok) throw new Error("Failed to search jobs");

      const data = await response.json();
      setJobs(data.jobs || []);
      
      if (data.jobs?.length === 0) {
        toast.info("No jobs found. Try different keywords.");
      } else {
        toast.success(`Found ${data.jobs.length} jobs matched to your profile!`);
      }
    } catch (error) {
      toast.error("Failed to search jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const findJobsForMe = async () => {
    if (!profile) {
      toast.error("Please complete your profile first");
      return;
    }

    if (!profile.job_titles?.length && !profile.skills?.length) {
      toast.error("Please add job titles or skills to your profile");
      return;
    }

    // Build smart query from profile
    const jobTitle = profile.job_titles?.[0] || "";
    const skills = profile.skills?.slice(0, 3).join(" ") || "";
    const smartQuery = jobTitle || skills;
    const smartLocation = profile.preferred_locations?.[0] || "";
    
    // Map job_type to employment type
    let empType = "";
    if (profile.job_type?.includes("full-time")) empType = "FULLTIME";
    else if (profile.job_type?.includes("part-time")) empType = "PARTTIME";
    else if (profile.job_type?.includes("contract")) empType = "CONTRACTOR";

    setQuery(smartQuery);
    setLocation(smartLocation);
    setEmploymentType(empType);

    await searchJobsWithParams(smartQuery, smartLocation, empType);
  };

  const searchJobs = async () => {
    if (!query.trim()) {
      toast.error("Please enter a search query");
      return;
    }

    await searchJobsWithParams(query, location, employmentType);
  };

  const getMatchScoreClass = (score) => {
    if (score >= 80) return "match-score-high";
    if (score >= 60) return "match-score-medium";
    return "match-score-low";
  };

  const handleApplyClick = (job) => {
    setSelectedJob(job);
    setOptimizedResume("");
    setCoverLetter("");
    setShowApplyDialog(true);
  };

  const generateOptimizedResume = async () => {
    if (!selectedJob) return;
    setGeneratingResume(true);
    try {
      const response = await fetch(`${API}/ai/optimize-resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_description: selectedJob.full_description || selectedJob.description,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to optimize resume");
      }

      const data = await response.json();
      setOptimizedResume(data.optimized_resume);
      toast.success("Resume optimized for ATS!");
    } catch (error) {
      toast.error(error.message || "Failed to optimize resume");
    } finally {
      setGeneratingResume(false);
    }
  };

  const generateCoverLetter = async () => {
    if (!selectedJob) return;
    setGeneratingCover(true);
    try {
      const response = await fetch(`${API}/ai/cover-letter`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_title: selectedJob.title,
          company: selectedJob.company,
          job_description: selectedJob.full_description || selectedJob.description,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate cover letter");
      }

      const data = await response.json();
      setCoverLetter(data.cover_letter);
      toast.success("Cover letter generated!");
    } catch (error) {
      toast.error(error.message || "Failed to generate cover letter");
    } finally {
      setGeneratingCover(false);
    }
  };

  const submitApplication = async () => {
    if (!selectedJob) return;
    setApplyLoading(true);
    try {
      const response = await fetch(`${API}/applications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_id: selectedJob.job_id,
          job_title: selectedJob.title,
          company: selectedJob.company,
          location: selectedJob.location,
          job_description: selectedJob.full_description || selectedJob.description,
        }),
      });

      if (!response.ok) throw new Error("Failed to save application");

      toast.success("Application saved! Review it in Applications.");
      setShowApplyDialog(false);
    } catch (error) {
      toast.error("Failed to save application");
    } finally {
      setApplyLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="job-search-page">
      <Navbar user={user} />
      
      <div className="hero-glow opacity-30" />

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">Find Your Perfect Job</h1>
          <p className="text-muted-foreground">
            Search thousands of jobs and get AI-powered match scores
          </p>
        </div>

        {/* Search Form */}
        <Card className="glass-light mb-8 animate-fade-in" data-testid="search-form">
          <CardContent className="p-6">
            {/* AI Find Jobs Button */}
            <div className="flex justify-center mb-6">
              <Button
                data-testid="find-jobs-for-me-btn"
                onClick={findJobsForMe}
                disabled={loading || initialLoading}
                className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 h-12 px-8 text-white font-medium"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                ) : (
                  <Wand2 className="w-5 h-5 mr-2" />
                )}
                Find Jobs For Me (AI-Powered)
              </Button>
            </div>

            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-sm text-muted-foreground">or search manually</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  data-testid="job-search-input"
                  placeholder="Job title, keywords, or company"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && searchJobs()}
                  className="pl-10 bg-white/5 border-white/10 h-12"
                />
              </div>
              <div className="relative md:w-48">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground z-10" />
                <Input
                  data-testid="location-input"
                  placeholder="Location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="pl-10 bg-white/5 border-white/10 h-12"
                />
              </div>
              <Select value={employmentType} onValueChange={setEmploymentType}>
                <SelectTrigger className="md:w-40 bg-white/5 border-white/10 h-12" data-testid="employment-type-select">
                  <SelectValue placeholder="Job Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="FULLTIME">Full-time</SelectItem>
                  <SelectItem value="PARTTIME">Part-time</SelectItem>
                  <SelectItem value="CONTRACTOR">Contract</SelectItem>
                  <SelectItem value="INTERN">Internship</SelectItem>
                </SelectContent>
              </Select>
              <Button
                data-testid="search-btn"
                onClick={searchJobs}
                disabled={loading}
                className="bg-indigo-500 hover:bg-indigo-600 h-12 px-8"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {initialLoading && (
          <div className="text-center py-16">
            <Loader2 className="w-12 h-12 text-indigo-400 mx-auto mb-4 animate-spin" />
            <p className="text-muted-foreground">Finding jobs matched to your profile...</p>
          </div>
        )}

        {/* Results */}
        {!initialLoading && jobs.length > 0 && (
          <div className="space-y-4" data-testid="job-results">
            <p className="text-muted-foreground">Found {jobs.length} jobs matched to your profile</p>
            {jobs.map((job, i) => (
              <Card
                key={job.job_id || i}
                data-testid={`job-card-${i}`}
                className="glass-light card-hover"
              >
                <CardContent className="p-6">
                  <div className="flex flex-col lg:flex-row lg:items-start gap-4">
                    {/* Company Logo */}
                    <div className="w-16 h-16 rounded-xl bg-white/5 flex items-center justify-center flex-shrink-0 overflow-hidden">
                      {job.company_logo ? (
                        <img
                          src={job.company_logo}
                          alt={job.company}
                          className="w-full h-full object-contain p-2"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.parentElement.innerHTML = `<span class="text-2xl font-bold text-indigo-400">${job.company?.charAt(0) || 'J'}</span>`;
                          }}
                        />
                      ) : (
                        <span className="text-2xl font-bold text-indigo-400">
                          {job.company?.charAt(0) || 'J'}
                        </span>
                      )}
                    </div>

                    {/* Job Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-foreground">{job.title}</h3>
                          <div className="flex items-center gap-2 text-muted-foreground mt-1">
                            <Building className="w-4 h-4" />
                            <span>{job.company}</span>
                          </div>
                        </div>
                        <Badge className={`${getMatchScoreClass(job.match_score)} px-3 py-1`}>
                          {job.match_score}% Match
                        </Badge>
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-3">
                        {job.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            <span>{job.location}</span>
                          </div>
                        )}
                        {job.employment_type && (
                          <div className="flex items-center gap-1">
                            <Briefcase className="w-4 h-4" />
                            <span className="capitalize">{job.employment_type.toLowerCase().replace('_', '-')}</span>
                          </div>
                        )}
                        {job.is_remote && (
                          <div className="flex items-center gap-1 text-emerald-400">
                            <Globe className="w-4 h-4" />
                            <span>Remote</span>
                          </div>
                        )}
                        {(job.salary_min || job.salary_max) && (
                          <div className="flex items-center gap-1">
                            <DollarSign className="w-4 h-4" />
                            <span>
                              {job.salary_min && `$${job.salary_min.toLocaleString()}`}
                              {job.salary_min && job.salary_max && ' - '}
                              {job.salary_max && `$${job.salary_max.toLocaleString()}`}
                            </span>
                          </div>
                        )}
                        {job.posted_at && (
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            <span>{new Date(job.posted_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>

                      <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                        {job.description}
                      </p>

                      <div className="flex flex-wrap gap-3">
                        <Button
                          data-testid={`apply-btn-${i}`}
                          onClick={() => handleApplyClick(job)}
                          className="bg-indigo-500 hover:bg-indigo-600"
                        >
                          <Sparkles className="w-4 h-4 mr-2" />
                          Quick Apply
                        </Button>
                        {job.apply_link && (
                          <Button
                            variant="outline"
                            className="border-white/10"
                            onClick={() => window.open(job.apply_link, '_blank')}
                          >
                            <ExternalLink className="w-4 h-4 mr-2" />
                            View Original
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !initialLoading && jobs.length === 0 && (
          <div className="text-center py-16" data-testid="empty-state">
            <Wand2 className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">Ready to Find Your Dream Job?</h3>
            <p className="text-muted-foreground max-w-md mx-auto mb-6">
              Click "Find Jobs For Me" to automatically discover opportunities matched to your profile, 
              or search manually using the fields above.
            </p>
            <Button
              onClick={findJobsForMe}
              disabled={loading}
              className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600"
            >
              <Wand2 className="w-4 h-4 mr-2" />
              Find Jobs For Me
            </Button>
          </div>
        )}
      </main>

      {/* Apply Dialog */}
      <Dialog open={showApplyDialog} onOpenChange={setShowApplyDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden bg-background border-white/10">
          <DialogHeader>
            <DialogTitle className="text-xl">
              Apply to {selectedJob?.title}
            </DialogTitle>
            <DialogDescription>
              {selectedJob?.company} • {selectedJob?.location}
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[60vh] pr-4">
            <div className="space-y-6 py-4">
              {/* Optimize Resume Section */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-foreground flex items-center gap-2">
                    <FileText className="w-5 h-5 text-emerald-400" />
                    ATS-Optimized Resume
                  </h4>
                  <Button
                    data-testid="generate-resume-btn"
                    size="sm"
                    onClick={generateOptimizedResume}
                    disabled={generatingResume}
                    className="bg-emerald-500 hover:bg-emerald-600"
                  >
                    {generatingResume ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      "Generate"
                    )}
                  </Button>
                </div>
                {optimizedResume && (
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                    <pre className="text-sm text-muted-foreground whitespace-pre-wrap font-sans">
                      {optimizedResume}
                    </pre>
                  </div>
                )}
              </div>

              {/* Cover Letter Section */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-foreground flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-indigo-400" />
                    Cover Letter
                  </h4>
                  <Button
                    data-testid="generate-cover-btn"
                    size="sm"
                    onClick={generateCoverLetter}
                    disabled={generatingCover}
                    className="bg-indigo-500 hover:bg-indigo-600"
                  >
                    {generatingCover ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      "Generate"
                    )}
                  </Button>
                </div>
                {coverLetter && (
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                    <pre className="text-sm text-muted-foreground whitespace-pre-wrap font-sans">
                      {coverLetter}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApplyDialog(false)}
              className="border-white/10"
            >
              Cancel
            </Button>
            <Button
              data-testid="submit-application-btn"
              onClick={submitApplication}
              disabled={applyLoading}
              className="bg-indigo-500 hover:bg-indigo-600"
            >
              {applyLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Save Application"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
