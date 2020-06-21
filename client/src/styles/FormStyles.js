import styled from "styled-components";

export const FormContainer = styled.form`
  display: flex;
  flex-direction: column;
  width: 320px;
  margin-bottom: 32px;
`;

export const FormInput = styled.input`
  all: unset;
  margin-bottom: 16px;
`;

export const SubmitButton = styled.button`
  all: unset;
  cursor: pointer;
  margin-bottom: 16px;
  padding: 8px 8px 8px 0;

  transition: 0.6s cubic-bezier(0.4, 0.8, 0.2, 1);
  background: linear-gradient(to left, #111111 50%, #ffffff 50%);
  background-size: 200% 100%;
  background-position: right bottom;

  &:hover {
    color: #111111;
    font-weight: 700;
    background-position: left bottom;
  }
`;
