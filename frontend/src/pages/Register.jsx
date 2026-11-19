import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { ArrowRight, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { BrandLogo } from '../components/common/BrandLogo';
import { Button } from '../components/common/Button';
import { InputField } from '../components/common/UI';
import { extractErrorMessage } from '../utils/formatters';

export function Register() {
  const { isAuthenticated, register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const validate = () => {
    const next = {};
    if (fullName.trim().length < 2) {
      next.fullName = 'Full name must be at least 2 characters.';
    }
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      next.email = 'Enter a valid email address.';
    }
    if (password.length < 8 || !/[a-zA-Z]/.test(password) || !/\d/.test(password)) {
      next.password = 'Password must be at least 8 characters and include letters and numbers.';
    }
    if (password !== confirmPassword) {
      next.confirmPassword = 'Passwords do not match.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setApiError('');
    try {
      await register(fullName.trim(), email.trim(), password);
      toast.success('Account created! Welcome to SprintFlow.');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setApiError(extractErrorMessage(err, 'Unable to create account.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-white">
      <div className="hidden lg:flex flex-col justify-between bg-[#101010] text-white p-12">
        <BrandLogo dark size="lg" />
        <div className="max-w-md space-y-6">
          <h2 className="text-3xl font-bold leading-tight">
            Built for small agile teams who ship <span className="text-[#75C900]">with clarity</span>.
          </h2>
          <ul className="space-y-3 text-sm text-neutral-300">
            {[
              'Create projects and invite 3–10 team members',
              'Break requirements into user stories and granular tasks',
              'Track progress with dynamic analytics & Kanban boards',
              'Receive automated upcoming and overdue deadline alerts',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#75C900] text-[#101010] flex items-center justify-center shrink-0 mt-0.5">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-neutral-500">
          SprintFlow — Agile Project Management Tool
        </p>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md space-y-6">
          <div className="lg:hidden">
            <BrandLogo dark={false} size="lg" />
          </div>

          <div>
            <h1 className="text-2xl font-bold text-[#101010]">Create your account</h1>
            <p className="text-sm text-[#737373] mt-1">
              Get started managing projects, stories, and tasks in seconds.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {apiError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs font-medium text-[#DC2626]">
                {apiError}
              </div>
            )}

            <InputField
              label="Full Name"
              required
              autoComplete="name"
              placeholder="e.g., Priya Nair"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              error={errors.fullName}
            />

            <InputField
              label="Work Email"
              type="email"
              required
              autoComplete="email"
              placeholder="priya@team.dev"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
            />

            <InputField
              label="Password"
              type="password"
              required
              autoComplete="new-password"
              placeholder="Min 8 chars, include letters & numbers"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
            />

            <InputField
              label="Confirm Password"
              type="password"
              required
              autoComplete="new-password"
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              error={errors.confirmPassword}
            />

            <Button type="submit" loading={submitting} size="lg" className="w-full mt-2">
              <span>Create Account</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </form>

          <p className="text-sm text-[#737373] text-center">
            Already registered?{' '}
            <Link
              to="/login"
              className="font-semibold text-[#101010] underline decoration-[#75C900] decoration-2 underline-offset-4 hover:text-[#66B000]"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
