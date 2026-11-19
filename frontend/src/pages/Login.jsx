import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, Layers, ShieldCheck, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { BrandLogo } from '../components/common/BrandLogo';
import { Button } from '../components/common/Button';
import { InputField } from '../components/common/UI';
import { extractErrorMessage } from '../utils/formatters';

export function Login() {
  const { isAuthenticated, login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    const next = {};
    if (!email.trim() || !email.includes('@')) next.email = 'Enter a valid email address.';
    if (!password) next.password = 'Password is required.';
    setErrors(next);
    if (Object.keys(next).length > 0) return;

    setSubmitting(true);
    setApiError('');
    try {
      await login(email.trim(), password);
      toast.success('Signed in to SprintFlow.');
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setApiError(extractErrorMessage(err, 'Invalid email or password.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-white">
      {/* Left dark brand panel */}
      <div className="hidden lg:flex flex-col justify-between bg-[#101010] text-white p-12">
        <BrandLogo dark size="lg" />
        <div className="max-w-md space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#171717] border border-neutral-800 text-xs font-medium text-[#75C900]">
            Agile Delivery for Focused Engineering Teams
          </div>
          <h2 className="text-3xl font-bold leading-tight">
            Structured execution from <span className="text-[#75C900]">Project</span> to{' '}
            <span className="text-[#75C900]">User Story</span> to{' '}
            <span className="text-[#75C900]">Task</span>.
          </h2>
          <p className="text-sm text-neutral-400 leading-relaxed">
            Plan sprints, coordinate 3–10 engineers, move work across Kanban columns, and stay ahead of deadlines with automated reminders.
          </p>
          <div className="space-y-3 pt-2">
            {[
              { icon: Layers, text: 'Hierarchical Project → User Story → Task tracking' },
              { icon: Zap, text: 'Real-time Kanban updates & background deadline reminders' },
              { icon: ShieldCheck, text: 'Role-scoped project access with JWT security' },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3 text-sm text-neutral-300">
                <span className="w-7 h-7 rounded-lg bg-[#171717] border border-neutral-800 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-[#75C900]" />
                </span>
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>
        <p className="text-xs text-neutral-500">
          SprintFlow — Independent Agile Project Management Workspace
        </p>
      </div>

      {/* Right form panel */}
      <div className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md space-y-7">
          <div className="lg:hidden">
            <BrandLogo dark={false} size="lg" />
          </div>

          <div>
            <h1 className="text-2xl font-bold text-[#101010]">Sign in to your workspace</h1>
            <p className="text-sm text-[#737373] mt-1">
              Enter your credentials to access your team projects and tasks.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {apiError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs font-medium text-[#DC2626]">
                {apiError}
              </div>
            )}

            <InputField
              label="Work Email"
              type="email"
              required
              autoComplete="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
            />

            <InputField
              label="Password"
              type="password"
              required
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
            />

            <Button type="submit" loading={submitting} size="lg" className="w-full mt-2">
              <span>Sign In</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </form>

          <p className="text-sm text-[#737373] text-center">
            New to SprintFlow?{' '}
            <Link
              to="/register"
              className="font-semibold text-[#101010] underline decoration-[#75C900] decoration-2 underline-offset-4 hover:text-[#66B000]"
            >
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
