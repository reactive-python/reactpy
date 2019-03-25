/**
 * Defines the React 16 Adapter for Enzyme.
 *
 * @link http://airbnb.io/enzyme/docs/installation/#working-with-react-16
 * @copyright 2017 Airbnb, Inc.
 */
const Adapter = require('enzyme-adapter-react-16');
import { configure } from 'enzyme';

configure({ adapter: new Adapter() });
